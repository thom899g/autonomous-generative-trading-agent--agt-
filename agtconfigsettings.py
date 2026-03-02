"""
Configuration management with environment variable validation.
Architectural Rationale: Centralized config prevents scattering API keys
across modules and enables runtime validation.
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    credentials_path: str
    project_id: str
    database_url: str
    
    def __post_init__(self):
        # Validate critical Firebase config
        if not os.path.exists(self.credentials_path):
            logger.error(f"Firebase credentials not found at {self.credentials_path}")
            raise FileNotFoundError(f"Firebase credentials file missing: {self.credentials_path}")
        
        if not all([self.project_id, self.database_url]):
            logger.critical("Firebase project ID and database URL must be set")
            raise ValueError("Incomplete Firebase configuration")

@dataclass
class ExchangeConfig:
    """Exchange API configuration with masking for logging"""
    name: str
    api_key: str
    api_secret: str
    
    @property
    def masked_key(self) -> str:
        """Safe representation for logging"""
        if self.api_key and len(self.api_key) > 8:
            return f"{self.api_key[:4]}...{self.api_key[-4:]}"
        return "****"
    
    def validate(self) -> bool:
        """Validate exchange credentials format"""
        if not self.api_key or not self.api_secret:
            logger.error(f"Invalid credentials for {self.name}")
            return False
        return True

class AGTConfig:
    """
    Singleton configuration manager ensuring single source of truth.
    Implements validation and default fallbacks for all critical parameters.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Environment
        self.environment = os.getenv("AGT_ENVIRONMENT", "development")
        
        # Firebase Configuration
        self.firebase = FirebaseConfig(
            credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
            project_id=os.getenv("FIREBASE_PROJECT_ID", ""),
            database_url=os.getenv("FIREBASE_DATABASE_URL", "")
        )
        
        # Exchange Configurations
        self.exchanges = {
            "binance": ExchangeConfig(
                name="binance",
                api_key=os.getenv("BINANCE_API_KEY", ""),
                api_secret=os.getenv("BINANCE_API_SECRET", "")
            )
        }
        
        # Trading Parameters
        self.max_position_size = float(os.getenv("AGT_MAX_POSITION_SIZE", "0.05"))
        self.update_interval_minutes = int(os.getenv("AGT_UPDATE_INTERVAL_MINUTES", "5"))
        
        # Validation
        self._validate()
        self._initialized = True
        logger.info(f"AGT Config initialized for {self.environment} environment")
    
    def _validate(self) -> None:
        """Validate all critical configurations"""
        errors = []
        
        # Validate Firebase
        try:
            self.firebase.__post_init__()
        except (FileNotFoundError, ValueError) as e:
            errors.append(f"Firebase config error: {e}")
        
        # Validate exchange credentials
        for exchange_name, exchange_config in self.exchanges.items():
            if not exchange_config.validate():
                errors.append(f"Exchange {exchange_name} config invalid")
        
        # Validate trading parameters
        if not 0 < self.max_position_size <= 0.5:
            errors.append(f"Invalid max_position_size: {self.max_position_size}. Must be 0-0.5")
        
        if errors:
            error_msg = "\n".join(errors)
            logger.critical(f"Configuration validation failed:\n{error_msg}")
            raise ValueError(f"Configuration errors: {error_msg}")