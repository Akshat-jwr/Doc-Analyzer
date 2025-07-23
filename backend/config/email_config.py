"""
📧 EMAIL CONFIGURATION
Centralized email settings with multiple provider support
"""
import os
from typing import Dict, Any
from enum import Enum

class EmailProvider(Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    SENDGRID = "sendgrid"
    CUSTOM_SMTP = "custom"

class EmailConfig:
    """🔧 Email Configuration Manager"""
    
    def __init__(self):
        self.provider = EmailProvider(os.getenv("EMAIL_PROVIDER", "gmail"))
        self.smtp_settings = self._get_smtp_settings()
        
        # ✅ TIMEOUT SETTINGS
        self.connection_timeout = int(os.getenv("EMAIL_CONNECTION_TIMEOUT", "15"))  # seconds
        self.send_timeout = int(os.getenv("EMAIL_SEND_TIMEOUT", "30"))  # seconds
        self.max_retries = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("EMAIL_RETRY_DELAY", "2"))  # seconds
        
        # ✅ CREDENTIALS
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        # ✅ OTP SETTINGS
        self.otp_expiry_minutes = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
        
    def _get_smtp_settings(self) -> Dict[str, Any]:
        """Get SMTP settings based on provider"""
        provider_settings = {
            EmailProvider.GMAIL: {
                "server": "smtp.gmail.com",
                "port": 587,
                "use_tls": True,
                "use_ssl": False
            },
            EmailProvider.OUTLOOK: {
                "server": "smtp-mail.outlook.com",
                "port": 587,
                "use_tls": True,
                "use_ssl": False
            },
            EmailProvider.SENDGRID: {
                "server": "smtp.sendgrid.net",
                "port": 587,
                "use_tls": True,
                "use_ssl": False
            },
            EmailProvider.CUSTOM_SMTP: {
                "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
                "use_ssl": os.getenv("SMTP_USE_SSL", "false").lower() == "true"
            }
        }
        
        return provider_settings.get(self.provider, provider_settings[EmailProvider.GMAIL])
    
    @property
    def smtp_server(self) -> str:
        return self.smtp_settings["server"]
    
    @property
    def smtp_port(self) -> int:
        return self.smtp_settings["port"]
    
    @property
    def use_tls(self) -> bool:
        return self.smtp_settings["use_tls"]
    
    @property
    def use_ssl(self) -> bool:
        return self.smtp_settings["use_ssl"]
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.smtp_email and self.smtp_password)
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information (without sensitive data)"""
        return {
            "provider": self.provider.value,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "connection_timeout": self.connection_timeout,
            "send_timeout": self.send_timeout,
            "max_retries": self.max_retries,
            "is_configured": self.is_configured(),
            "smtp_email_configured": bool(self.smtp_email),
            "smtp_password_configured": bool(self.smtp_password)
        }

# Singleton instance
email_config = EmailConfig()
