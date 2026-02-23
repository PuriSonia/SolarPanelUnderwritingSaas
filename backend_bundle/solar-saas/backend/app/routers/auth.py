from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Organization
from ..security import hash_password, verify_password, create_access_token
from ..schemas import RegisterRequest, LoginRequest
from ..audit import log_event

router = APIRouter(tags=["Auth"])

@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organization(name=data.org_name, billing_status="trialing")
    db.add(org)
    db.commit()
    db.refresh(org)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        org_id=org.id,
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_event(db, user=user, org_id=org.id, action="user.register", entity="User", entity_id=str(user.id), metadata={"email": user.email})

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    log_event(db, user=user, org_id=user.org_id, action="user.login", entity="User", entity_id=str(user.id))
    return {"access_token": token, "token_type": "bearer"}
