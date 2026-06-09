"""
Shared FastAPI dependencies: current user retrieval.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.security import decode_access_token
from backend.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    sub = decode_access_token(token)
    if sub is None:
        raise cred_exc
    user = db.query(User).filter(User.username == sub).first()
    if user is None or not user.is_active:
        raise cred_exc
    return user
