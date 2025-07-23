from typing import Optional, Dict, Any
import logging
import asyncio
from utils.pydantic_objectid import PyObjectId

from models.user import User
from .otp_service import otp_service
from .jwt_service import jwt_service

logger = logging.getLogger(__name__)

class AuthService:
    
    async def send_login_otp(self, email: str) -> Dict[str, Any]:
        """Send OTP for login/registration with timeout protection"""
        try:
            # Create OTP first (this is fast)
            otp_code = await otp_service.create_otp(email, purpose="login")
            
            # Try to send email with timeout protection
            try:
                email_sent = await asyncio.wait_for(
                    otp_service.send_otp_email(email, otp_code, purpose="login"),
                    timeout=10.0  # 10 second timeout for API response
                )
                
                if email_sent:
                    return {
                        "success": True,
                        "message": "OTP sent successfully to your email"
                    }
                else:
                    # Email failed but don't block API response
                    logger.warning(f"Direct email failed for {email}, OTP still created")
                    return {
                        "success": True,
                        "message": "OTP created. If you don't receive it, please try again.",
                        "note": "Email delivery may be delayed"
                    }
                    
            except asyncio.TimeoutError:
                # Email is taking too long - don't block the API response
                logger.warning(f"Email timeout for {email}, but OTP created")
                
                # Try background sending as fallback
                try:
                    from services.background_email_service import background_email_service
                    await background_email_service.queue_email(email, otp_code, "login")
                    logger.info(f"Email queued for background delivery to {email}")
                except:
                    pass  # Background service failed too, but don't break the flow
                
                return {
                    "success": True,
                    "message": "OTP created. Email delivery in progress...",
                    "note": "If you don't receive the email within 2 minutes, please try again"
                }
                
        except Exception as e:
            logger.error(f"Error in send_login_otp: {e}")
            return {
                "success": False,
                "message": "An error occurred. Please try again."
            }
    
    async def verify_login_otp(self, email: str, otp_code: str) -> Dict[str, Any]:
        """Verify OTP and login/register user"""
        try:
        # Verify OTP
            is_valid = await otp_service.verify_otp(email, otp_code, purpose="login")
        
            if not is_valid:
                return {
                    "success": False,
                    "message": "Invalid or expired OTP"
             }
        
            # Check if user exists
            user = await self.get_user_by_email(email)
        
            if not user:
                # Create new user
                user = await self.create_user(email)
        
            # Create user data with correct field names for UserResponse
            user_data = {
                "id": str(user.id),           # Changed from "user_id" to "id"
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active   # Added missing field
            }
        
            # Create JWT token data (separate from response user data)
            jwt_user_data = {
                "user_id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name
            }
        
            tokens = jwt_service.create_token_pair(jwt_user_data)
        
            return {
                "success": True,
                "message": "Login successful",
                "user": user_data,  # This now matches UserResponse structure
                **tokens
            }
            
        except Exception as e:
            logger.error(f"Error verifying login OTP: {e}")
            return {
                "success": False,
                "message": "An error occurred during login"
            }
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            return await User.find_one(User.email == email)
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            if not PyObjectId.is_valid(user_id):
                return None
            return await User.get(PyObjectId(user_id))
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def create_user(self, email: str) -> User:
        """Create new user"""
        try:
            # Generate username from email
            username = email.split('@')[0]
            base_username = username
            counter = 1
            
            # Ensure username is unique
            while await self._username_exists(username):
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user
            user = User(
                email=email,
                username=username,
                full_name=email.split('@')[0].title(),
                is_active=True
            )
            
            await user.insert()
            logger.info(f"Created new user: {email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def _username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        try:
            existing_user = await User.find_one(User.username == username)
            return existing_user is not None
        except Exception as e:
            logger.error(f"Error checking username existence: {e}")
            return False
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt_service.verify_token(refresh_token)
        
            if not payload or payload.get("type") != "refresh":
                return {
                    "success": False,
                    "message": "Invalid refresh token"
                }
        
            # Get user
            user_id = payload.get("user_id")
            user = await self.get_user_by_id(user_id)
        
            if not user or not user.is_active:
                return {
                    "success": False,
                    "message": "User not found or inactive"
                }
        
            # Create JWT token data
            jwt_user_data = {
                "user_id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name
            }
        
            tokens = jwt_service.create_token_pair(jwt_user_data)
        
            return {
                "success": True,
                "message": "Token refreshed successfully",
                **tokens
         }
        
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return {
                "success": False,
                "message": "An error occurred during token refresh"
            }

# Singleton instance
auth_service = AuthService()
