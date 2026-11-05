import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.notifications import send_user_notification
from app.schemas import UserCreate, UserResponse, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


def validate_user_id(user_id: str) -> None:
    try:
        UUID(user_id)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid user ID format.")


def get_user_or_404(db: Session, user_id: str) -> User:
    validate_user_id(user_id)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


def user_snapshot(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name, email=str(payload.email).lower(), role=payload.role)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists.",
        )
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating user.")
        raise HTTPException(status_code=500, detail="Unable to create user.")

    send_user_notification("USER_CREATED", user_snapshot(user))
    return user


@router.get("", response_model=list[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if skip < 0 or limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="skip must be >= 0 and limit must be between 1 and 500.")
    return db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    return get_user_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    changes = payload.model_dump(exclude_unset=True)

    if not changes or all(value is None for value in changes.values()):
        raise HTTPException(status_code=400, detail="Provide at least one field to update.")

    if "email" in changes and changes["email"] is not None:
        changes["email"] = str(changes["email"]).lower()

    for field, value in changes.items():
        if value is not None:
            setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A user with this email already exists.")
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while updating user %s.", user_id)
        raise HTTPException(status_code=500, detail="Unable to update user.")

    send_user_notification("USER_UPDATED", user_snapshot(user))
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    deleted_user = user_snapshot(user)

    try:
        db.delete(user)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while deleting user %s.", user_id)
        raise HTTPException(status_code=500, detail="Unable to delete user.")

    send_user_notification("USER_DELETED", deleted_user)
    return {"message": "User deleted successfully.", "user": deleted_user}
