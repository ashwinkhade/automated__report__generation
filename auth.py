"""Authentication routes: register, login, current-user."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.core.database import get_db
from backend.core.security import hash_password, verify_password, create_access_token
from backend.models.user import User
from backend.schemas.user import UserCreate, UserOut, Token
from backend.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(User)
        .filter(or_(User.email == payload.email, User.username == payload.username))
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already registered.")
    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.username)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(or_(User.username == form.username, User.email == form.username))
        .first()
    )
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive.")
    token = create_access_token(user.username)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current
