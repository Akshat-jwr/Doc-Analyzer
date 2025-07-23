"""
🚀 BACKGROUND EMAIL SERVICE
Non-blocking email service that won't affect API response times
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class BackgroundEmailService:
    """📤 BACKGROUND: Email service that runs in background"""
    
    def __init__(self):
        self.email_queue = asyncio.Queue()
        self.is_running = False
        self.stats = {
            "emails_queued": 0,
            "emails_sent": 0,
            "emails_failed": 0,
            "last_activity": None
        }
    
    async def start_background_worker(self):
        """🔄 START: Background email worker"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("📤 Starting background email worker")
        
        # Run the worker in background
        asyncio.create_task(self._email_worker())
    
    async def _email_worker(self):
        """⚙️ WORKER: Process email queue in background"""
        from auth.otp_service import otp_service
        
        while self.is_running:
            try:
                # Wait for email task with timeout
                email_task = await asyncio.wait_for(
                    self.email_queue.get(), 
                    timeout=60.0  # Check every minute
                )
                
                email_address = email_task["email"]
                otp_code = email_task["otp_code"]
                purpose = email_task["purpose"]
                attempt = email_task.get("attempt", 1)
                
                logger.info(f"📤 Processing email for {email_address} (attempt {attempt})")
                
                # Try to send email
                success = await otp_service.send_otp_email_async(email_address, otp_code, purpose)
                
                if success:
                    self.stats["emails_sent"] += 1
                    logger.info(f"✅ Background email sent to {email_address}")
                else:
                    # Retry up to 3 times
                    if attempt < 3:
                        email_task["attempt"] = attempt + 1
                        await asyncio.sleep(5)  # Wait 5 seconds before retry
                        await self.email_queue.put(email_task)
                        logger.warning(f"🔄 Retrying email for {email_address} (attempt {attempt + 1})")
                    else:
                        self.stats["emails_failed"] += 1
                        logger.error(f"❌ Failed to send email to {email_address} after 3 attempts")
                
                self.stats["last_activity"] = datetime.now().isoformat()
                
            except asyncio.TimeoutError:
                # No emails in queue - continue waiting
                continue
            except Exception as e:
                logger.error(f"❌ Background email worker error: {e}")
                await asyncio.sleep(5)  # Wait before continuing
    
    async def queue_email(self, email: str, otp_code: str, purpose: str = "login") -> Dict[str, Any]:
        """📥 QUEUE: Add email to background queue"""
        try:
            email_task = {
                "email": email,
                "otp_code": otp_code,
                "purpose": purpose,
                "queued_at": datetime.now().isoformat(),
                "attempt": 1
            }
            
            await self.email_queue.put(email_task)
            self.stats["emails_queued"] += 1
            
            logger.info(f"📥 Email queued for {email}")
            
            return {
                "success": True,
                "message": "Email queued for delivery",
                "queued": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error queueing email: {e}")
            return {
                "success": False,
                "message": "Failed to queue email",
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """📊 STATS: Get email service statistics"""
        return {
            **self.stats,
            "queue_size": self.email_queue.qsize(),
            "is_running": self.is_running
        }
    
    async def stop(self):
        """🛑 STOP: Stop background worker"""
        self.is_running = False
        logger.info("📤 Stopped background email worker")

# Global instance
background_email_service = BackgroundEmailService()
