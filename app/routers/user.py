from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from backend.db_depends import get_db

from sqlalchemy.future import select

from backend.db import Base

from typing import List, Annotated
from models import User, Task
from schemas import CreateUser, UpdateUser
from sqlalchemy import insert, update, delete
from slugify import slugify
import uuid


# Создаем роутер с префиксом "/user" и тегом "user" для группировки связанных маршрутов
router = APIRouter(prefix="/user", tags=["user"])

def generate_unique_slug(username: str, db: Session) -> str:
    """Генерация уникального slug."""
    base_slug = slugify(username)
    unique_slug = base_slug
    counter = 1
    # Проверка на существование slug в базе
    while db.execute(select(User).where(User.slug == unique_slug)).scalars().first():
        unique_slug = f"{base_slug}-{counter}"
        counter += 1
    return unique_slug

@router.get("/")
async def all_users(db: Annotated[Session, Depends(get_db)]):
    # Получаем всех пользователей из базы данных
    users = db.scalars(select(User)).all()
    return users  # Возвращаем список пользователей


@router.get("/user/{user_id}")
async def user_by_id(user_id: int, db: Annotated[Session, Depends(get_db)]):
    # Извлекаем запись пользователя по user_id
    user = db.execute(select(User).where(User.id == user_id)).scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User was not found")

    return user  # Возвращаем найденного пользователя

@router.get("/{user_id}/tasks")
async def tasks_by_user_id(user_id: int, db: Annotated[Session, Depends(get_db)]):
    # Получаем все задачи для конкретного пользователя
    tasks = db.scalars(select(Task).where(Task.user_id == user_id)).all()
    return tasks  # Возвращаем список задач


@router.post("/create")
async def create_user(db: Annotated[Session, Depends(get_db)], user: CreateUser):
    # Проверка на существующего пользователя
    existing_user = db.execute(select(User).where(User.username == user.username)).scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this username already exists")

    # Создание пользователя
    db.execute(insert(User).values(
        username=user.username,
        firstname=user.firstname,
        lastname=user.lastname,
        age=user.age,
        slug=slugify(user.username)
    ))

    db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.put("/update/{user_id}")
async def update_user(
        user_id: int,
        user: UpdateUser,
        db: Annotated[Session, Depends(get_db)]
):
    existing_user = db.scalar(select(User).where(User.id == user_id))

    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found"
        )

    db.execute(update(User).where(User.id == user_id).values(
        firstname=user.firstname,
        lastname=user.lastname,
        age=user.age,
        slug=slugify(user.firstname)
    ))

    db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'User update is successful!'
    }


@router.delete("/delete")
async def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    existing_user = db.scalar(select(User).where(User.id == user_id))
    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User was not found"
        )

    # Удаление всех задач, связанных с пользователем
    db.execute(delete(Task).where(Task.user_id == user_id))

    # Удаление пользователя
    db.execute(delete(User).where(User.id == user_id))
    db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'User and associated tasks were successfully deleted'
    }
