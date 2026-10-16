from fastapi import APIRouter, Path, HTTPException, status, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from model import Todo, TodoItem, TodoItems

todo_router = APIRouter()
todo_list: list[Todo] = []

templates = Jinja2Templates(directory="templates/")

@todo_router.post("/todo")
async def add_todo(request: Request, todo: Todo = Depends(Todo.as_form)):
    cleaned = todo.item.strip() if todo.item else ""

    if not cleaned:
        return templates.TemplateResponse(
            request=request,
            name="todo.html",
            context={
                "todos": todo_list,
                "error": "Поле не может быть пустым. Введите текст задачи.",
                "item": todo.item or ""
            },
            status_code=400
        )

    if len(cleaned) > 200:
        return templates.TemplateResponse(
            request=request,
            name="todo.html",
            context={
                "todos": todo_list,
                "error": "Задача слишком длинная (максимум 200 символов).",
                "item": cleaned
            },
            status_code=400
        )

    todo.item = cleaned
    todo.id = len(todo_list) + 1
    todo_list.append(todo)

    return RedirectResponse(url="/todo", status_code=status.HTTP_303_SEE_OTHER)

@todo_router.get("/todo")
async def retrieve_todo(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="todo.html",
        context={"todos": todo_list}
    )

@todo_router.get("/todo/{todo_id}")
async def get_single_todo(
    request: Request,
    todo_id: int = Path(..., title="ID задачи для получения")
):
    for todo in todo_list:
        if todo.id == todo_id:
            return templates.TemplateResponse(
                request=request,
                name="todo.html",
                context={"todo": todo}
            )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Задача с указанным ID не найдена (разработчик Ivanov I.I.)"
    )

