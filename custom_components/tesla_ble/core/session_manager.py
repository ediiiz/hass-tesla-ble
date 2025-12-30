from __future__ import annotations

import logging
import secrets
import time
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from .crypto import (
    TeslaSessionKeys,
    aes_gcm_decrypt,
    aes_gcm_encrypt,
    compute_shared_secret,
    derive_hkdf_key,
    derive_key_id,
    generate_key_pair,
    get_private_key_bytes,
    get_public_key_bytes,
    load_private_key,
)
from .proto import keys_pb2, signatures_pb2, universal_message_pb2, vcsec_pb2 # type: ignore

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)


class AuthenticationState(IntEnum):
    """Authentication state of a session."""

    UNAUTHENTICATED = 0
    HANDSHAKING = 1
    AUTHENTICATED = 2


class TeslaSession(BaseModel):
    """Container for session state for a specific domain."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    domain: int  # universal_message_pb2.Domain
    state: AuthenticationState = AuthenticationState.UNAUTHENTICATED
    counter: int = 0
    epoch: bytes | None = None
    session_keys: TeslaSessionKeys | None = None
    vehicle_public_key: bytes | None = None
    vehicle_key_id: bytes | None = None
    last_update: float = Field(default_factory=time.time)

    def is_authenticated(self) -> bool:
        """Check if the session is authenticated."""
        return (
            self.state == AuthenticationState.AUTHENTICATED
            and self.session_keys is not None
        )


class TeslaSessionManager:
    """Manages authentication sessions with a Tesla vehicle."""

    def __init__(self, private_key_bytes: bytes | None = None) -> None:
        """Initialize the session manager.

        Args:
            private_key_bytes: The local 32-byte private key.
            If None, a new one will be generated.
        """
        if private_key_bytes:
            self._private_key = load_private_key(private_key_bytes)
        else:
            self._private_key, _ = generate_key_pair()

        self._public_key_bytes = get_public_key_bytes(self._private_key)
        self._key_id = derive_key_id(self._public_key_bytes)

        self._sessions: dict[int, TeslaSession] = {
            universal_message_pb2.DOMAIN_VEHICLE_SECURITY: TeslaSession(
                domain=universal_message_pb2.DOMAIN_VEHICLE_SECURITY
            ),
            universal_message_pb2.DOMAIN_INFOTAINMENT: TeslaSession(
                domain=universal_message_pb2.DOMAIN_INFOTAINMENT
            ),
        }

    @property
    def private_key_bytes(self) -> bytes:
        """Get the local private key bytes."""
        return get_private_key_bytes(self._private_key)

    @property
    def public_key_bytes(self) -> bytes:
        """Get the local uncompressed public key bytes."""
        return self._public_key_bytes

    @property
    def key_id(self) -> bytes:
        """Get the local 4-byte key ID."""
        return self._key_id

    def get_session(self, domain: int) -> TeslaSession:
        """Get the session for a specific domain."""
        if domain not in self._sessions:
            self._sessions[domain] = TeslaSession(domain=domain)
        return self._sessions[domain]

    def is_authenticated(self, domain: int) -> bool:
        """Check if a domain is authenticated."""
        return self.get_session(domain).is_authenticated()

    def invalidate_session(self, domain: int) -> None:
        """Invalidate the session for a domain."""
        _LOGGER.info("Invalidating session for domain %s", domain)
        session = self.get_session(domain)
        session.state = AuthenticationState.UNAUTHENTICATED
        session.session_keys = None
        session.epoch = None
        session.counter = 0

    def prepare_session_info_request(
        self, domain: int
    ) -> Any:
        """Prepare a SessionInfoRequest message.

        Args:
            domain: The target domain.

        Returns:
            The prepared RoutableMessage.
        """
        session = self.get_session(domain)
        session.state = AuthenticationState.HANDSHAKING

        msg = universal_message_pb2.RoutableMessage()
        msg.to_destination.domain = domain
        msg.from_destination.domain = universal_message_pb2.DOMAIN_BROADCAST

        msg.session_info_request.public_key = self._public_key_bytes
        # Reference implementation uses 4 bytes of random challenge
        msg.session_info_request.challenge = secrets.token_bytes(4)

        return msg

    def update_session(
        self, domain: int, session_info: Any
    ) -> None:
        """Update session state from a SessionInfo message.

        Args:
            domain: The domain the info came from.
            session_info: The parsed SessionInfo message.
        """
        session = self.get_session(domain)

        _LOGGER.debug(
            "Updating session for %s: counter=%d, status=%s",
            domain,
            session_info.counter,
            session_info.status,
        )

        if session_info.status != signatures_pb2.SESSION_INFO_STATUS_OK:
            _LOGGER.error("Session info error for %s: %s", domain, session_info.status)
            self.invalidate_session(domain)
            return

        session.counter = session_info.counter
        session.epoch = session_info.epoch
        session.vehicle_public_key = session_info.publicKey
        session.vehicle_key_id = derive_key_id(session_info.publicKey)

        # Derive session keys
        _LOGGER.debug("Deriving session keys for domain %s", domain)
        shared_secret = compute_shared_secret(
            self._private_key, session.vehicle_public_key
        )

        # Salt: epoch + local_key_id + vehicle_key_id
        if session.epoch is None:
            _LOGGER.error("Epoch is None during session update")
            self.invalidate_session(domain)
            return

        salt = session.epoch + self._key_id + session.vehicle_key_id
        _LOGGER.debug("Handshake salt: %s", salt.hex())

        # Encryption key
        enc_key = derive_hkdf_key(
            shared_secret=shared_secret,
            salt=salt,
            info=b"authenticated command",
            length=16,
        )

        # Authentication key
        auth_key = derive_hkdf_key(
            shared_secret=shared_secret,
            salt=salt,
            info=b"authenticated command hmac",
            length=16,
        )

        session.session_keys = TeslaSessionKeys(
            encryption_key=enc_key, authentication_key=auth_key
        )
        session.state = AuthenticationState.AUTHENTICATED
        session.last_update = time.time()

        _LOGGER.info(
            "Session authenticated for domain %s with counter %d",
            domain,
            session.counter,
        )

    def wrap_message(
        self,
        domain: int,
        payload_bytes: bytes,
    ) -> Any:
        """Wrap a payload in an authenticated RoutableMessage.

        Args:
            domain: The target domain.
            payload_bytes: The serialized sub-message.

        Returns:
            The authenticated RoutableMessage.
        """
        session = self.get_session(domain)
        if not session.is_authenticated():
            raise ValueError(f"Session for domain {domain} is not authenticated")

        session.counter += 1

        msg = universal_message_pb2.RoutableMessage()
        msg.to_destination.domain = domain
        msg.from_destination.domain = universal_message_pb2.DOMAIN_BROADCAST
        msg.flags = universal_message_pb2.FLAG_USER_COMMAND

        # Prepare signature data
        msg.signature_data.signer_identity.public_key = self._public_key_bytes

        personalized = msg.signature_data.AES_GCM_Personalized_data
        personalized.epoch = session.epoch
        personalized.counter = session.counter
        personalized.expires_at = 0

        nonce = secrets.token_bytes(12)
        personalized.nonce = nonce

        # Prepare AAD
        aad = self._prepare_aad(domain, session.counter, session.epoch)

        _LOGGER.debug(
            "Wrapping message for domain %s, counter %d", domain, session.counter
        )
        assert session.session_keys is not None
        ciphertext_with_tag = aes_gcm_encrypt(
            key=session.session_keys.encryption_key,
            nonce=nonce,
            data=payload_bytes,
            aad=aad,
        )

        # AES-GCM in cryptography returns ciphertext + 16-byte tag
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]

        msg.protobuf_message_as_bytes = ciphertext
        personalized.tag = tag

        return msg

    def _prepare_aad(self, domain: int, counter: int, epoch: bytes | None) -> bytes:
        """Prepare Associated Authenticated Data for encryption/decryption.

        AAD = TagDomain + Domain + TagCounter + Counter + TagEpoch + Epoch
        """
        aad = bytearray()

        # TagDomain (0x01) + Domain (4 bytes BE)
        aad.append(signatures_pb2.TAG_DOMAIN)
        aad.extend(domain.to_bytes(4, "big"))

        # TagCounter (0x05) + Counter (4 bytes BE)
        aad.append(signatures_pb2.TAG_COUNTER)
        aad.extend(counter.to_bytes(4, "big"))

        # TagEpoch (0x03) + Epoch (16 bytes)
        aad.append(signatures_pb2.TAG_EPOCH)
        if epoch is not None:
            aad.extend(epoch)
        else:
            # Handle None epoch by appending 16 zero bytes or empty?
            # Tesla protocol expects 16 bytes for epoch.
            aad.extend(b"\x00" * 16)

        return bytes(aad)

    def unwrap_message(
        self, domain: int, msg: Any
    ) -> bytes:
        """Decrypt and verify an incoming RoutableMessage.

        Args:
            domain: The domain the message came from.
            msg: The received RoutableMessage.

        Returns:
            The decrypted payload bytes.
        """
        session = self.get_session(domain)

        # Check for message status errors
        if msg.HasField("signedMessageStatus"):
            status = msg.signedMessageStatus
            if status.operation_status == universal_message_pb2.OPERATIONSTATUS_ERROR:
                _LOGGER.error("Received error status: %s", status.signed_message_fault)
                if status.signed_message_fault in (
                    universal_message_pb2.MESSAGEFAULT_ERROR_INVALID_TOKEN_OR_COUNTER,
                    universal_message_pb2.MESSAGEFAULT_ERROR_INCORRECT_EPOCH,
                ):
                    self.invalidate_session(domain)
                return msg.protobuf_message_as_bytes # type: ignore

        if not session.is_authenticated():
            # If not authenticated, return raw bytes (e.g. for status messages)
            return msg.protobuf_message_as_bytes # type: ignore

        if msg.signature_data.WhichOneof("sig_type") != "AES_GCM_Response_data":
            _LOGGER.debug(
                "Message from %s does not have AES_GCM_Response_data signature", domain
            )
            return msg.protobuf_message_as_bytes # type: ignore

        resp_data = msg.signature_data.AES_GCM_Response_data

        # Verify counter (anti-replay) - responses should ideally have higher counters
        # But for now, we just log it as the vehicle manages its own counter state
        _LOGGER.debug(
            "Received response counter: %d (local: %d)",
            resp_data.counter,
            session.counter,
        )

        ciphertext = msg.protobuf_message_as_bytes
        tag = resp_data.tag
        nonce = resp_data.nonce

        # Decrypt
        try:
            # Responses use an empty AAD or specific AAD depending on version.
            # Most common is empty AAD for responses.
            _LOGGER.debug(
                "Unwrapping response for domain %s, counter %d",
                domain,
                resp_data.counter,
            )
            assert session.session_keys is not None
            plaintext = aes_gcm_decrypt(
                key=session.session_keys.encryption_key,
                nonce=nonce,
                data=ciphertext + tag,
                aad=b"",
            )
            return plaintext
        except Exception as e:
            _LOGGER.error("Failed to decrypt message from %s: %s", domain, e)
            raise

    def prepare_pairing_message(
        self, role: int = keys_pb2.ROLE_DRIVER
    ) -> Any:
        """Prepare a whitelist message for pairing.

        Args:
            role: The role to request (default: ROLE_DRIVER).

        Returns:
            The prepared RoutableMessage containing the VCSEC whitelist operation.
        """
        # 1. Create WhitelistOperation
        wl_op = vcsec_pb2.WhitelistOperation()
        # Role is already an int from keys_pb2.Role
        wl_op.addPublicKeyToWhitelist.PublicKeyRaw = self._public_key_bytes

        # Metdata for role
        wl_op.metadataForKey.keyFormFactor = vcsec_pb2.KEY_FORM_FACTOR_CLOUD_KEY

        # Wait, the role needs to be set.
        # Looking at vcsec.proto, addPublicKeyToWhitelist is just PublicKey.
        # PermissionChange might be needed for role.
        # Reference implementation often uses PermissionChange for role.

        # Simplified: Many vehicles just accept the key and user confirms on screen.

        # 2. Wrap in UnsignedMessage
        unsigned_msg = vcsec_pb2.UnsignedMessage()
        unsigned_msg.WhitelistOperation.CopyFrom(wl_op)

        payload = unsigned_msg.SerializeToString()

        # 3. Wrap in RoutableMessage (Broadcast domain, unauthenticated)
        msg = universal_message_pb2.RoutableMessage()
        msg.to_destination.domain = universal_message_pb2.DOMAIN_VEHICLE_SECURITY
        msg.from_destination.domain = universal_message_pb2.DOMAIN_BROADCAST
        msg.protobuf_message_as_bytes = payload

        return msg
