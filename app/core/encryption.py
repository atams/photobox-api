import base64
import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from typing import Any
from app.core.config import settings


class AESEncryption:
    def __init__(self):
        # Use static key and IV from settings for security
        self.key = self._get_encryption_key()
        self.iv = self._get_encryption_iv()

    def _get_encryption_key(self) -> bytes:
        """Get encryption key from settings"""
        key = settings.ENCRYPTION_KEY
        # Ensure exactly 32 bytes for AES-256
        if len(key) >= 32:
            return key[:32].encode('utf-8')
        else:
            # Pad with zeros if too short
            return (key + '0' * (32 - len(key))).encode('utf-8')

    def _get_encryption_iv(self) -> bytes:
        """Get encryption IV from settings"""
        iv = settings.ENCRYPTION_IV
        # Ensure exactly 16 bytes for AES block size
        if len(iv) >= 16:
            return iv[:16].encode('utf-8')
        else:
            # Pad with zeros if too short
            return (iv + '0' * (16 - len(iv))).encode('utf-8')

    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime, Decimal, and UUID objects"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, UUID):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def encrypt_data(self, data: Any) -> str:
        """
        Encrypt any JSON-serializable data
        Returns base64 encoded encrypted string
        """
        try:
            # Convert data to JSON string with custom serializer for datetime
            json_string = json.dumps(data, ensure_ascii=False, separators=(',', ':'), default=self._json_serializer)

            # Create cipher with static key and IV
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # Pad data to AES block size (16 bytes)
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(json_string.encode('utf-8'))
            padded_data += padder.finalize()

            # Encrypt
            encrypted = encryptor.update(padded_data) + encryptor.finalize()

            # Encode to base64 for JSON transport
            return base64.b64encode(encrypted).decode('utf-8')

        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")

    def decrypt_data(self, encrypted_data: str) -> Any:
        """
        Decrypt data (for testing purposes)
        In production, this will be done on frontend
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)

            # Create cipher with static key and IV
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            decryptor = cipher.decryptor()

            # Decrypt
            decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()

            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted_padded)
            decrypted += unpadder.finalize()

            # Convert back to JSON
            json_string = decrypted.decode('utf-8')
            return json.loads(json_string)

        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")


# Global instance
encryption = AESEncryption()
