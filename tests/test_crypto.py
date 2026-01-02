"""Unit tests for the Tesla BLE crypto module."""

from cryptography.hazmat.primitives.asymmetric import ec

from custom_components.tesla_ble.core import crypto


def test_generate_key_pair():
    """Test key generation."""
    private_key, public_key_bytes = crypto.generate_key_pair()

    assert isinstance(private_key, ec.EllipticCurvePrivateKey)
    # P-256 Uncompressed point should be 65 bytes (0x04 + 32X + 32Y)
    assert len(public_key_bytes) == 65
    assert public_key_bytes[0] == 0x04


def test_load_private_key():
    """Test loading a private key from bytes."""
    private_key, _ = crypto.generate_key_pair()
    private_bytes = crypto.get_private_key_bytes(private_key)

    loaded_key = crypto.load_private_key(private_bytes)
    loaded_bytes = crypto.get_private_key_bytes(loaded_key)

    assert private_bytes == loaded_bytes


def test_derive_key_id():
    """Test Key ID derivation."""
    _, public_key_bytes = crypto.generate_key_pair()
    key_id = crypto.derive_key_id(public_key_bytes)
    assert len(key_id) == 4


def test_ecdh_exchange():
    """Test ECDH shared secret computation."""
    # Alice
    alice_priv, alice_pub = crypto.generate_key_pair()
    # Bob
    bob_priv, bob_pub = crypto.generate_key_pair()

    # Alice computes shared secret using Bob's public key
    alice_shared = crypto.compute_shared_secret(alice_priv, bob_pub)

    # Bob computes shared secret using Alice's public key
    bob_shared = crypto.compute_shared_secret(bob_priv, alice_pub)

    assert alice_shared == bob_shared


def test_hkdf_derivation():
    """Test HKDF key derivation."""
    shared_secret = b"shared_secret" * 2
    salt = b"salt" * 4
    info = b"test info"

    key1 = crypto.derive_hkdf_key(shared_secret, salt, info, 16)
    key2 = crypto.derive_hkdf_key(shared_secret, salt, info, 16)

    assert len(key1) == 16
    assert key1 == key2

    # Different context should produce different keys
    key3 = crypto.derive_hkdf_key(shared_secret, salt, b"other info", 16)
    assert key1 != key3


def test_aes_gcm_roundtrip():
    """Test AES-GCM encryption and decryption."""
    # 16-byte key for AES-128 or 32-byte for AES-256
    key = b"0123456789abcdef"
    nonce = b"112233445566"
    data = b"Hello Tesla!"
    aad = b"header data"

    ciphertext_with_tag = crypto.aes_gcm_encrypt(key, nonce, data, aad)

    # Decrypt
    plaintext = crypto.aes_gcm_decrypt(key, nonce, ciphertext_with_tag, aad)
    assert plaintext == data


def test_hmac_sha256():
    """Test HMAC signing and verification."""
    key = b"secret_key"
    data = b"message"

    signature = crypto.compute_hmac_sha256(key, data)
    assert len(signature) == 32  # SHA256 size

    assert crypto.verify_hmac_sha256(key, data, signature)
    assert not crypto.verify_hmac_sha256(key, data + b"corrupt", signature)
    assert not crypto.verify_hmac_sha256(b"wrong_key", data, signature)
