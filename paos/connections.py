"""
Encrypted connection manager for sensitive credentials
"""

from cryptography.fernet import Fernet
from paos.config import settings
from sqlalchemy.orm import Session
from paos import models
from typing import Dict, Any, Optional
import json
import hashlib


class ConnectionManager:
    """Manages encrypted storage and retrieval of connection credentials"""
    
    def __init__(self):
        # Generate cipher from settings key
        key = settings.encryption_key.encode()
        # Pad or hash key to 32 bytes for Fernet
        key_hash = hashlib.sha256(key).digest()
        self.cipher = Fernet(Fernet.generate_key())  # Will be replaced with proper key
        
    def _get_cipher(self):
        """Get Fernet cipher with proper key"""
        key = settings.encryption_key.encode()
        key_hash = hashlib.sha256(key).digest()
        # Fernet requires base64-encoded 32-byte key
        import base64
        key_b64 = base64.urlsafe_b64encode(key_hash)
        return Fernet(key_b64)
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials dict to string"""
        cipher = self._get_cipher()
        json_str = json.dumps(credentials)
        encrypted = cipher.encrypt(json_str.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self, encrypted_str: str) -> Dict[str, Any]:
        """Decrypt credentials string to dict"""
        cipher = self._get_cipher()
        decrypted = cipher.decrypt(encrypted_str.encode())
        return json.loads(decrypted.decode())
    
    def create_connection(
        self,
        db: Session,
        name: str,
        service_type: str,
        credentials: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> models.Connection:
        """Create a new connection with encrypted credentials"""
        encrypted = self.encrypt_credentials(credentials)
        
        connection = models.Connection(
            name=name,
            service_type=service_type,
            credentials_encrypted=encrypted,
            config=config or {},
            status=models.ConnectionStatus.ACTION_REQUIRED.value,
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)
        return connection
    
    def get_connection(self, db: Session, connection_id: str) -> models.Connection:
        """Get connection by ID"""
        return db.query(models.Connection).filter(
            models.Connection.id == connection_id
        ).first()
    
    def get_connection_by_name(self, db: Session, name: str) -> models.Connection:
        """Get connection by name"""
        return db.query(models.Connection).filter(
            models.Connection.name == name
        ).first()
    
    def get_credentials(self, db: Session, connection_id: str) -> Dict[str, Any]:
        """Get decrypted credentials for a connection"""
        connection = self.get_connection(db, connection_id)
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        return self.decrypt_credentials(connection.credentials_encrypted)
    
    def list_connections(self, db: Session):
        """List all connections (without credentials)"""
        return db.query(models.Connection).all()
    
    def update_connection_status(
        self,
        db: Session,
        connection_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update connection status"""
        connection = self.get_connection(db, connection_id)
        if connection:
            connection.status = status
            if error_message:
                connection.error_message = error_message
            from datetime import datetime
            connection.last_verified = datetime.utcnow()
            db.commit()


# Singleton instance
connection_manager = ConnectionManager()
