from __future__ import annotations

import logging
from typing import Final

from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import BaseModel, ConfigDict

_LOGGER = logging.getLogger(__name__)

# Tesla uses NIST P-256 (SECP256R1)
CURVE: Final = ec.SECP256R1()
PUBLIC_KEY_SIZE: Final = 65  # Uncompressed: 0x04 + 32 bytes X + 32 bytes Y
PRIVATE_KEY_SIZE: Final = 32  # raw bytes


def generate_key_pair() -> tuple[ec.EllipticCurvePrivateKey, bytes]:
    """Generate a new NIST P-256 key pair.

    Returns:
        A tuple containing the private key object and the uncompressed public key bytes.
    """
    private_key = ec.generate_private_key(CURVE)
    public_key_bytes = private_key.public_key().public_bytes(
        encoding=Encoding.X962, format=PublicFormat.UncompressedPoints
    )
    return private_key, public_key_bytes


def load_private_key(private_key_bytes: bytes) -> ec.EllipticCurvePrivateKey:
    """Load a NIST P-256 private key from raw bytes.

    Args:
        private_key_bytes: The 32-byte private key.

    Returns:
        The private key object.
    """

    # We expect 32 bytes of raw private key
    if len(private_key_bytes) != PRIVATE_KEY_SIZE:
        raise ValueError(f"Invalid private key size: {len(private_key_bytes)}")

    return ec.derive_private_key(int.from_bytes(private_key_bytes, "big"), CURVE)


def get_private_key_bytes(private_key: ec.EllipticCurvePrivateKey) -> bytes:
    """Get the raw private key bytes.

    Args:
        private_key: The private key object.

    Returns:
        The 32-byte private key.
    """
    return private_key.private_numbers().private_value.to_bytes(PRIVATE_KEY_SIZE, "big") # type: ignore


def get_public_key_bytes(private_key: ec.EllipticCurvePrivateKey) -> bytes:
    """Get the uncompressed public key bytes from a private key.

    Args:
        private_key: The private key object.

    Returns:
        The 65-byte uncompressed public key.
    """
    return private_key.public_key().public_bytes(
        encoding=Encoding.X962, format=PublicFormat.UncompressedPoints
    )


def derive_key_id(public_key_bytes: bytes) -> bytes:
    """Derive the 4-byte Key ID from a public key.

    Args:
        public_key_bytes: The uncompressed public key.

    Returns:
        The first 4 bytes of the SHA1 hash of the public key.
    """
    digest = hashes.Hash(hashes.SHA1())
    digest.update(public_key_bytes)
    return digest.finalize()[:4]


class TeslaSessionKeys(BaseModel):
    """Container for derived session keys."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    encryption_key: bytes
    authentication_key: bytes


def compute_shared_secret(
    private_key: ec.EllipticCurvePrivateKey, peer_public_key_bytes: bytes
) -> bytes:
    """Compute the ECDH shared secret.

    Args:
        private_key: The local private key.
        peer_public_key_bytes: The peer's uncompressed public key.

    Returns:
        The shared secret bytes (X coordinate of the agreement).
    """
    _LOGGER.debug(
        "Computing shared secret with peer public key: %s", peer_public_key_bytes.hex()
    )
    peer_public_key = ec.EllipticCurvePublicNumbers.from_encoded_point( # type: ignore
        CURVE, peer_public_key_bytes
    ).public_key()
    shared_secret = private_key.exchange(ec.ECDH(), peer_public_key)
    return shared_secret


def derive_hkdf_key(
    shared_secret: bytes, salt: bytes | None, info: bytes, length: int
) -> bytes:
    """Derive a key using HKDF-SHA256.

    Args:
        shared_secret: The input keying material.
        salt: Optional salt.
        info: Context and application specific information.
        length: Desired output key length in bytes.

    Returns:
        The derived key.
    """
    _LOGGER.debug("Deriving HKDF key with info: %s, salt: %s", info, salt.hex() if salt else "None")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    )
    return hkdf.derive(shared_secret)


def aes_gcm_encrypt(
    key: bytes, nonce: bytes, data: bytes, aad: bytes | None = None
) -> bytes:
    """Encrypt data using AES-GCM.

    Args:
        key: 16 or 32 byte AES key.
        nonce: 12 byte initialization vector.
        data: Plaintext data.
        aad: Optional associated authenticated data.

    Returns:
        The ciphertext followed by the 16-byte authentication tag.
    """
    aesgcm = AESGCM(key)
    return aesgcm.encrypt(nonce, data, aad)


def aes_gcm_decrypt(
    key: bytes, nonce: bytes, data: bytes, aad: bytes | None = None
) -> bytes:
    """Decrypt data using AES-GCM.

    Args:
        key: 16 or 32 byte AES key.
        nonce: 12 byte initialization vector.
        data: Ciphertext with appended 16-byte tag.
        aad: Optional associated authenticated data.

    Returns:
        The decrypted plaintext.
    """
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, data, aad)


def compute_hmac_sha256(key: bytes, data: bytes) -> bytes:
    """Compute HMAC-SHA256 signature.

    Args:
        key: The HMAC key.
        data: The data to sign.

    Returns:
        The 32-byte HMAC signature.
    """
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(data)
    return h.finalize()


def verify_hmac_sha256(key: bytes, data: bytes, signature: bytes) -> bool:
    """Verify HMAC-SHA256 signature.

    Args:
        key: The HMAC key.
        data: The signed data.
        signature: The signature to verify.

    Returns:
        True if valid, False otherwise.
    """
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(data)
    try:
        h.verify(signature)
        return True
    except Exception:
        return False
