from fastapi import APIRouter, Path, HTTPException
from model import Todo, TodoItem

todo_router = APIRouter()

todo_list = []


@todo_router.post("/todo", summary="Добавить новую задачу")
async def add_todo(todo: Todo) -> dict:
    for existing in todo_list:
        if existing.id == todo.id:
            raise HTTPException(
                status_code=400,
                detail=f"Задача с id={todo.id} уже существует."
            )
    todo_list.append(todo)
    return {"message": f"Задача '{todo.item}' успешно добавлена с id={todo.id}."}


@todo_router.get("/todo", summary="Получить все задачи")
async def retrieve_todos() -> dict:
    return {
        "total": len(todo_list),
        "todos": todo_list
    }


@todo_router.get("/todo/{todo_id}", summary="Получить задачу по id")
async def get_single_todo(
    todo_id: int = Path(..., title="ID задачи для поиска", ge=1)
) -> dict:
    for todo in todo_list:
        if todo.id == todo_id:
            return {"todo": todo}
    raise HTTPException(
        status_code=404,
        detail=f"Задача с id={todo_id} не найдена."
    )


@todo_router.put("/todo/{todo_id}", summary="Обновить задачу по id")
async def update_todo(
    todo_data: TodoItem,
    todo_id: int = Path(..., title="ID задачи для обновления", ge=1)
) -> dict:
    for todo in todo_list:
        if todo.id == todo_id:
            todo.item = todo_data.item
            return {"message": f"Задача с id={todo_id} успешно обновлена."}
    raise HTTPException(
        status_code=404,
        detail=f"Задача с id={todo_id} не найдена."
    )


@todo_router.delete("/todo/{todo_id}", summary="Удалить задачу по id")
async def delete_todo(
    todo_id: int = Path(..., title="ID задачи для удаления", ge=1)
) -> dict:
    for index, todo in enumerate(todo_list):
        if todo.id == todo_id:
            todo_list.pop(index)
            return {"message": f"Задача с id={todo_id} успешно удалена."}
    raise HTTPException(
        status_code=404,
        detail=f"Задача с id={todo_id} не найдена."
    )