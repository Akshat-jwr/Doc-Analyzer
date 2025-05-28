import random
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import logging

from .models import OTP

load_dotenv()
logger = logging.getLogger(__name__)

class OTPService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.otp_expiry_minutes = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
        
        if not self.smtp_email or not self.smtp_password:
            logger.warning("SMTP credentials not found. Email sending will be disabled.")
    
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
    
    async def send_otp_email(self, email: str, otp_code: str, purpose: str = "login") -> bool:
        """Send OTP via email"""
        if not self.smtp_email or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
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
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_email, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"OTP email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending OTP email to {email}: {e}")
            return False

# Singleton instance
otp_service = OTPService()
