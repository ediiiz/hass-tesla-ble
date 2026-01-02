"""
Core models for Tesla BLE integration.
"""

from pydantic import BaseModel, SecretStr


class TeslaSession(BaseModel):
    """
    Stores the cryptographic material and sync state for a vehicle session.
    """

    vehicle_vin: str
    private_key: SecretStr  # Local private key (PEM format)
    public_key: str  # Local public key (Hex encoded)
    vehicle_public_key: str  # Vehicle's public key (Hex encoded)

    # Counter synchronization
    counter: int = 0
    epoch: bytes = b""

    def get_private_key_bytes(self) -> bytes:
        """
        Returns the raw private key bytes.
        """
        return self.private_key.get_secret_value().encode("utf-8")
