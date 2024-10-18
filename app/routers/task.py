from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from backend.db_depends import get_db
from sqlalchemy.future import select
from models import Task, User  # Добавляем модель Task
from schemas import CreateTask, UpdateTask  # Добавляем схемы для создания и обновления задач
from sqlalchemy import insert, update, delete
from typing import List, Annotated
from slugify import slugify

# Создаем роутер с префиксом "/task" и тегом "task" для группировки связанных маршрутов
router = APIRouter(prefix="/task", tags=["task"])

@router.get("/")
async def all_tasks(db: Annotated[Session, Depends(get_db)]):
    # Получаем все задачи из базы данных
    tasks = db.scalars(select(Task)).all()
    return tasks  # Возвращаем список задач

@router.get("/task/{task_id}")
async def task_by_id(task_id: int, db: Annotated[Session, Depends(get_db)]):
    # Извлекаем запись задачи по task_id
    task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task was not found")
    return task  # Возвращаем найденную задачу

@router.post("/create")
async def create_task(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    task: CreateTask
):
    # Проверка на существующего пользователя
    existing_user = db.execute(select(User).where(User.id == user_id)).scalars().first()
    if existing_user is None:
        raise HTTPException(status_code=404, detail="User was not found")

    # Создание задачи
    db.execute(insert(Task).values(
        title=task.title,
        content=task.content,
        priority=task.priority,
        user_id=user_id,  # Устанавливаем связь с пользователем
        slug=slugify(task.title)  # Генерируем slug на основе заголовка задачи
    ))
    db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }



@router.put("/update/{task_id}")
async def update_task(
        task_id: int, task: UpdateTask,
        db: Annotated[Session, Depends(get_db)]):
    existing_task = db.scalar(select(Task).where(Task.id == task_id))
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task was not found"
        )

    db.execute(update(Task).where(Task.id == task_id).values(
        title=task.title,
        content=task.content,
        priority=task.priority,
        slug=slugify(task.title)
    ))
    db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Task update is successful!'
    }


@router.delete("/delete")
async def delete_task(
        task_id: int,
        db: Annotated[Session, Depends(get_db)]
):
    # Проверка на существующую задачу
    existing_task = db.scalar(select(Task).where(Task.id == task_id))
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task was not found"
        )

    # Удаление задачи
    db.execute(delete(Task).where(Task.id == task_id))
    db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Task was successfully deleted'
    }
