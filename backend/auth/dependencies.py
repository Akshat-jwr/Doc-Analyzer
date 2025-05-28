from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from utils.pydantic_objectid import PyObjectId

from .jwt_service import jwt_service
from .auth_service import auth_service
from models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = jwt_service.verify_token(credentials.credentials)
        
        if payload is None or payload.get("type") != "access":
            raise credentials_exception
        
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        # Get user from database
        user = await auth_service.get_user_by_id(user_id)
        
        if user is None or not user.is_active:
            raise credentials_exception
        
        return user
        
    except Exception:
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Optional dependency - returns None if no auth
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    
    if not credentials:
        return None
    
    try:
        payload = jwt_service.verify_token(credentials.credentials)
        
        if payload is None or payload.get("type") != "access":
            return None
        
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        
        user = await auth_service.get_user_by_id(user_id)
        
        if user is None or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None
