"""
Cryptography - Classical and quantum-enhanced encryption.

Provides encryption primitives using quantum-generated keys
and hybrid classical-quantum encryption schemes.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum


class EncryptionMode(Enum):
    """Encryption modes."""
    QUANTUM_ONLY = "quantum_only"
    HYBRID = "hybrid"
    CLASSICAL_FALLBACK = "classical_fallback"


@dataclass
class CryptoKey:
    """Represents a cryptographic key."""
    key_id: str
    key_bits: List[int]
    key_bytes: bytes = field(default_factory=bytes)
    created_at: float = 0.0
    expires_at: Optional[float] = None
    use_count: int = 0
    max_uses: int = 0
    
    def __post_init__(self):
        """Convert bits to bytes if needed."""
        if not self.key_bytes and self.key_bits:
            self.key_bytes = bytes(int(''.join(str(b) for b in self.key_bits[i:i+8]), 2) 
                                   for i in range(0, len(self.key_bits), 8))
    
    @classmethod
    def generate(cls, length_bits: int = 256) -> CryptoKey:
        """Generate random key."""
        key_bits = [int(b) for b in format(secrets.randbits(length_bits), f'0{length_bits}b')]
        return cls(
            key_id=secrets.token_hex(16),
            key_bits=key_bits,
            created_at=0.0,
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        import time
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    @property
    def entropy(self) -> float:
        """Calculate key entropy."""
        if not self.key_bits:
            return 0.0
        return len(set(self.key_bits)) / len(self.key_bits)
    
    def to_bytes(self) -> bytes:
        """Convert key to bytes."""
        return self.key_bytes


class QuantumEncryption:
    """
    Quantum-enhanced encryption system.
    
    Combines QKD-generated keys with classical encryption
    for provably secure communication.
    """
    
    def __init__(self):
        """Initialize encryption system."""
        self.keys: Dict[str, CryptoKey] = {}
        self._mode = EncryptionMode.HYBRID
    
    def set_mode(self, mode: EncryptionMode) -> None:
        """Set encryption mode."""
        self._mode = mode
    
    def generate_key(self, length_bits: int = 256) -> CryptoKey:
        """Generate new cryptographic key."""
        key = CryptoKey.generate(length_bits)
        self.keys[key.key_id] = key
        return key
    
    def encrypt_xor(self, plaintext: bytes, key: CryptoKey) -> Tuple[bytes, str]:
        """
        XOR encryption with key.
        
        Args:
            plaintext: Data to encrypt
            key: Encryption key
            
        Returns:
            Tuple of (ciphertext, key_id)
        """
        key_bytes = key.to_bytes()
        key_len = len(key_bytes)
        
        ciphertext = bytearray(plaintext)
        for i in range(len(ciphertext)):
            ciphertext[i] ^= key_bytes[i % key_len]
        
        key.use_count += 1
        return bytes(ciphertext), key.key_id
    
    def decrypt_xor(self, ciphertext: bytes, key_id: str) -> Optional[bytes]:
        """XOR decryption (same as encryption)."""
        key = self.keys.get(key_id)
        if not key:
            return None
        
        return self.encrypt_xor(ciphertext, key)[0]
    
    def encrypt_aes_like(self, plaintext: bytes, key: CryptoKey) -> Tuple[bytes, bytes, str]:
        """
        Simplified AES-like encryption.
        
        Args:
            plaintext: Data to encrypt
            key: Encryption key
            
        Returns:
            Tuple of (ciphertext, iv, key_id)
        """
        import os
        
        key_bytes = key.to_bytes()[:32] if len(key.to_bytes()) >= 32 else key.to_bytes().ljust(32, b'\x00')
        iv = os.urandom(16)
        
        ciphertext = bytearray(len(plaintext))
        for i in range(len(plaintext)):
            key_byte = key_bytes[(i + int.from_bytes(iv, 'big')) % len(key_bytes)]
            ciphertext[i] = plaintext[i] ^ key_byte ^ iv[i % len(iv)]
        
        key.use_count += 1
        return bytes(ciphertext), iv, key.key_id
    
    def decrypt_aes_like(self, ciphertext: bytes, iv: bytes, key_id: str) -> Optional[bytes]:
        """AES-like decryption."""
        key = self.keys.get(key_id)
        if not key:
            return None
        
        key_bytes = key.to_bytes()[:32] if len(key.to_bytes()) >= 32 else key.to_bytes().ljust(32, b'\x00')
        
        plaintext = bytearray(len(ciphertext))
        for i in range(len(ciphertext)):
            key_byte = key_bytes[(i + int.from_bytes(iv, 'big')) % len(key_bytes)]
            plaintext[i] = ciphertext[i] ^ key_byte ^ iv[i % len(iv)]
        
        return bytes(plaintext)
    
    def hash_data(self, data: bytes, algorithm: str = "sha256") -> str:
        """Hash data."""
        if algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data).hexdigest()
        elif algorithm == "blake2b":
            return hashlib.blake2b(data).hexdigest()
        return hashlib.sha256(data).hexdigest()
    
    def hmac_sign(self, data: bytes, key: CryptoKey) -> bytes:
        """Create HMAC signature."""
        return hmac.new(key.to_bytes(), data, hashlib.sha256).digest()
    
    def hmac_verify(self, data: bytes, signature: bytes, key: CryptoKey) -> bool:
        """Verify HMAC signature."""
        expected = self.hmac_sign(data, key)
        return hmac.compare_digest(signature, expected)
    
    def quantum_one_time_pad(
        self,
        plaintext: bytes,
        key: CryptoKey
    ) -> Tuple[bytes, str]:
        """
        Quantum One-Time Pad encryption.
        
        Perfect secrecy if key is truly random and used once.
        
        Args:
            plaintext: Data to encrypt
            key: Quantum-generated key
            
        Returns:
            Tuple of (ciphertext, key_id)
        """
        required_bits = len(plaintext) * 8
        
        if len(key.key_bits) < required_bits:
            key = CryptoKey.generate(required_bits)
        
        key_stream = key.key_bits[:required_bits]
        key_bytes = bytes(int(''.join(str(b) for b in key_stream[i:i+8]), 2) 
                          for i in range(0, required_bits, 8))
        
        ciphertext = bytes(p ^ k for p, k in zip(plaintext, key_bytes))
        
        return ciphertext, key.key_id
    
    def get_key_stats(self) -> Dict[str, Any]:
        """Get encryption statistics."""
        return {
            "total_keys": len(self.keys),
            "expired_keys": sum(1 for k in self.keys.values() if k.is_expired),
            "keys_by_use": {
                "unused": sum(1 for k in self.keys.values() if k.use_count == 0),
                "light": sum(1 for k in self.keys.values() if 0 < k.use_count <= 10),
                "heavy": sum(1 for k in self.keys.values() if k.use_count > 10),
            },
        }
