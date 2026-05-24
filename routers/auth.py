from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import uuid

from database.postgres import get_db_connection, get_user_by_email, insert_user
from services.auth_service import get_password_hash, verify_password, create_access_token, create_refresh_token, verify_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserCreate(BaseModel):
    email: str
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str

@router.post("/register")
def register_user(user: UserCreate):
    conn = get_db_connection()
    try:
        existing = get_user_by_email(conn, user.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        user_id = str(uuid.uuid4())
        hashed_pw = get_password_hash(user.password)
        insert_user(conn, user_id, user.email, hashed_pw)
        conn.commit()
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    try:
        user = get_user_by_email(conn, form_data.username) # OAuth2 uses 'username' field
        if not user or not verify_password(form_data.password, user['hashed_password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user['id']})
        refresh_token = create_refresh_token(data={"sub": user['id']})
        
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    finally:
        conn.close()

@router.post("/refresh")
def refresh_access_token(token_data: TokenRefresh):
    try:
        payload = verify_token(token_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        user_id = payload.get("sub")
        access_token = create_access_token(data={"sub": user_id})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
