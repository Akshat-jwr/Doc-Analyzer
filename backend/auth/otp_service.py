import random
import smtplib
import os
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import logging
import socket

from .models import OTP
from config.email_config import email_config

load_dotenv()
logger = logging.getLogger(__name__)

class OTPService:
    def __init__(self):
        # ✅ USE CENTRALIZED EMAIL CONFIG
        self.config = email_config
        
        # Legacy compatibility
        self.smtp_server = self.config.smtp_server
        self.smtp_port = self.config.smtp_port
        self.smtp_email = self.config.smtp_email
        self.smtp_password = self.config.smtp_password
        self.otp_expiry_minutes = self.config.otp_expiry_minutes
        
        # ✅ TIMEOUT CONFIGURATION
        self.smtp_timeout = self.config.send_timeout
        self.connection_timeout = self.config.connection_timeout
        self.max_retries = self.config.max_retries
        
        if not self.config.is_configured():
            logger.warning("⚠️ SMTP credentials not found. Email sending will be disabled.")
            logger.info(f"📧 Email config debug: {self.config.get_debug_info()}")
        else:
            logger.info(f"✅ Email service configured: {self.config.provider.value} via {self.smtp_server}:{self.smtp_port}")
    
    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    async def create_otp(self, email: str, purpose: str = "login") -> str:
        """Create and store OTP in database"""
        # Invalidate any existing unused OTPs for this email and purpose
        await self._invalidate_existing_otps(email, purpose)
        
        # Generate new OTP
        otp_code = self.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
        
        # Store in database
        otp_record = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at,
            purpose=purpose
        )
        
        await otp_record.insert()
        logger.info(f"OTP created for {email} with purpose {purpose}")
        return otp_code
    
    async def verify_otp(self, email: str, otp_code: str, purpose: str = "login") -> bool:
        """Verify OTP and mark as used"""
        try:
            # Find valid OTP
            otp_record = await OTP.find_one(
                OTP.email == email,
                OTP.otp_code == otp_code,
                OTP.purpose == purpose,
                OTP.is_used == False,
                OTP.expires_at > datetime.utcnow()
            )
            
            if otp_record:
                # Mark as used
                otp_record.is_used = True
                await otp_record.save()
                logger.info(f"OTP verified successfully for {email}")
                return True
            else:
                logger.warning(f"Invalid or expired OTP for {email}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False
    
    async def _invalidate_existing_otps(self, email: str, purpose: str):
        """Mark existing unused OTPs as used"""
        try:
            existing_otps = await OTP.find(
                OTP.email == email,
                OTP.purpose == purpose,
                OTP.is_used == False
            ).to_list()
            
            for otp in existing_otps:
                otp.is_used = True
                await otp.save()
            
            if existing_otps:
                logger.info(f"Invalidated {len(existing_otps)} existing OTPs for {email}")
            
        except Exception as e:
            logger.error(f"Error invalidating existing OTPs: {e}")
    
    async def send_otp_email_async(self, email: str, otp_code: str, purpose: str = "login") -> bool:
        """🚀 ASYNC: Send OTP via email with proper timeout handling"""
        if not self.config.is_configured():
            logger.error("❌ SMTP credentials not configured")
            return False
        
        for attempt in range(self.max_retries):
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = self.smtp_email
                msg['To'] = email
                msg['Subject'] = f"Your OTP for {purpose.title()}"
                
                # Email body
                body = f"""
Hello,

Your OTP for {purpose} is: {otp_code}

This OTP will expire in {self.otp_expiry_minutes} minutes.

If you didn't request this, please ignore this email.

Best regards,
Document Intelligence Team
                """
                
                msg.attach(MIMEText(body, 'plain'))
                
                # ✅ ASYNC EMAIL SENDING WITH TIMEOUT
                try:
                    # Use aiosmtplib for async email sending
                    await asyncio.wait_for(
                        aiosmtplib.send(
                            msg,
                            hostname=self.smtp_server,
                            port=self.smtp_port,
                            start_tls=self.config.use_tls,
                            use_tls=self.config.use_ssl,
                            username=self.smtp_email,
                            password=self.smtp_password,
                            timeout=self.connection_timeout
                        ),
                        timeout=self.smtp_timeout
                    )
                    
                    logger.info(f"✅ OTP email sent successfully to {email} (attempt {attempt + 1})")
                    return True
                    
                except ImportError:
                    # Fallback to synchronous method with timeout
                    logger.warning("⚠️ aiosmtplib not available, using sync method with timeout")
                    return await self._send_email_sync_with_timeout(msg, email, attempt + 1)
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Email timeout on attempt {attempt + 1} for {email}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"❌ Email sending failed after {self.max_retries} attempts: Timeout")
                    return False
                    
            except Exception as e:
                logger.warning(f"⚠️ Email attempt {attempt + 1} failed for {email}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay ** attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"❌ Email sending failed after {self.max_retries} attempts: {e}")
                    return False
        
        return False
    
    async def _send_email_sync_with_timeout(self, msg, email: str, attempt: int) -> bool:
        """🔄 FALLBACK: Synchronous email with timeout"""
        try:
            def send_sync():
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.connection_timeout)
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)
                server.quit()
                return True
            
            # Run sync operation with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, send_sync),
                timeout=self.smtp_timeout
            )
            
            logger.info(f"✅ OTP email sent successfully to {email} (sync method, attempt {attempt})")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Sync email timeout for {email}")
            return False
        except Exception as e:
            logger.error(f"❌ Sync email error for {email}: {e}")
            return False
    
    async def test_email_connection(self) -> dict:
        """🔧 TEST: Email connection without sending actual email"""
        if not self.config.is_configured():
            return {
                "success": False,
                "error": "SMTP credentials not configured",
                "config": self.config.get_debug_info()
            }
        
        try:
            # Test basic connection first
            import socket
            
            # Test socket connection
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex((self.smtp_server, self.smtp_port))
                sock.close()
                
                if result != 0:
                    return {
                        "success": False,
                        "error": f"Cannot reach {self.smtp_server}:{self.smtp_port} (firewall/network issue)",
                        "config": self.config.get_debug_info()
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Socket connection failed: {str(e)}",
                    "config": self.config.get_debug_info()
                }
            
            # Test SMTP connection
            try:
                smtp_client = aiosmtplib.SMTP(
                    hostname=self.smtp_server, 
                    port=self.smtp_port, 
                    timeout=self.connection_timeout
                )
                await asyncio.wait_for(smtp_client.connect(), timeout=self.smtp_timeout)
                await smtp_client.quit()
                
                logger.info(f"✅ Email connection test successful")
                return {
                    "success": True,
                    "message": "Email connection successful",
                    "config": self.config.get_debug_info()
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"SMTP connection failed: {str(e)}",
                    "config": self.config.get_debug_info()
                }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Connection timeout - check network/firewall settings",
                "config": self.config.get_debug_info()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}",
                "config": self.config.get_debug_info()
            }
    
    async def send_test_email(self, email: str) -> dict:
        """🧪 TEST: Send a test email"""
        try:
            result = await self.send_otp_email_async(email, "123456", "test")
            return {
                "success": result,
                "message": "Test email sent" if result else "Test email failed",
                "config": self.config.get_debug_info()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Test email failed: {str(e)}",
                "config": self.config.get_debug_info()
            }
    
    async def send_otp_email(self, email: str, otp_code: str, purpose: str = "login") -> bool:
        """📧 MAIN: Send OTP email (backward compatibility)"""
        return await self.send_otp_email_async(email, otp_code, purpose)

# Singleton instance
otp_service = OTPService()
