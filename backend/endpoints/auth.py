from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from auth import auth_service, get_current_active_user
from models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Request models
class SendOTPRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Response models
class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    is_active: bool

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: UserResponse = None
    access_token: str = None
    refresh_token: str = None
    token_type: str = None

@router.post("/send-otp")
async def send_otp(request: SendOTPRequest):
    """Send OTP to email for login/registration"""
    result = await auth_service.send_login_otp(request.email)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return {"message": result["message"]}

@router.post("/verify-otp", response_model=LoginResponse)
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and login/register user"""
    result = await auth_service.verify_login_otp(
        request.email, 
        request.otp_code
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return LoginResponse(**result)

@router.post("/refresh-token")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    result = await auth_service.refresh_token(request.refresh_token)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )
    
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"]
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout user (client should delete tokens)"""
    return {"message": "Logged out successfully"}
