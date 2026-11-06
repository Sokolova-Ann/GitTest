from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from beanie import PydanticObjectId
from typing import List
from bson import ObjectId # Для конвертации ID

from models import Todo, User, UserSignIn
from database import Database

templates = Jinja2Templates(directory="templates")
todo_db = Database(Todo)
user_db = Database(User)

router = APIRouter()

# --- Вспомогательная функция проверки текущего пользователя (через Cookie) ---
def get_current_user(request: Request) -> str:
    email = request.cookies.get("user_session")
    if not email:
        return None
    return email


# ==================== ВЕБ-ИНТЕРФЕЙС (Todo) ====================

@router.get("/")
async def home(request: Request):
    user_email = get_current_user(request)
    
    # Если не вошел — показываем страницу входа
    if not user_email:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    # Ищем только задачи этого пользователя в MongoDB
    todos = await Todo.find(Todo.owner_email == user_email).to_list()
    
    return templates.TemplateResponse(
        request=request,
        name="todo.html",
        context={"todos": todos, "user": user_email}
    )

@router.post("/todo")
async def add_todo(request: Request, item: str = Form(...)):
    user_email = get_current_user(request)
    if not user_email:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if not item.strip():
        todos = await Todo.find(Todo.owner_email == user_email).to_list()
        return templates.TemplateResponse(
            request=request,
            name="todo.html",
            context={"todos": todos, "user": user_email, "error": "Поле не может быть пустым"}
        )
    
    new_todo = Todo(item=item.strip(), owner_email=user_email)
    await todo_db.save(new_todo)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/todo/{id}/delete")
async def delete_todo(id: str):
    await todo_db.delete(id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


# ==================== ВЕБ-ИНТЕРФЕЙС (Авторизация) ====================

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"error": None})

@router.post("/register")
async def register_user(request: Request, email: str = Form(...), password: str = Form(...)):
    user_exist = await User.find_one(User.email == email)
    if user_exist:
        return templates.TemplateResponse(
            request=request, name="register.html", context={"error": "Этот email уже занят"}
        )
    
    new_user = User(email=email, password=password, is_admin=False)
    await user_db.save(new_user)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@router.post("/login")
async def login_user(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await User.find_one(User.email == email)
    if not user or user.password != password:
        return templates.TemplateResponse(
            request=request, name="login.html", context={"error": "Неверный email или пароль"}
        )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_session", value=email, httponly=True)
    return response

@router.get("/logout")
async def logout_user():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("user_session")
    return response


# ==================== REST API (для Swagger) ====================
# (Оставляем как было)
@router.post("/api/todo", response_model=Todo, tags=["API"])
async def api_create_todo(body: Todo):
    await todo_db.save(body)
    return body

@router.get("/api/todo", response_model=List[Todo], tags=["API"])
async def api_get_todos():
    return await todo_db.get_all()


# ==================== АДМИН-ПАНЕЛЬ ====================
# (Оставляем как было)
def require_admin(request: Request):
    email = request.cookies.get("admin_session")
    if not email or email != "admin@test.com":
         raise HTTPException(status_code=403, detail="Нет прав")
    return email

@router.get("/admin/login")
async def admin_login_form(request: Request):
    return templates.TemplateResponse(request=request, name="admin_login.html", context={"error": None})

@router.post("/admin/login")
async def admin_login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await User.find_one(User.email == email)
    if not user or not user.is_admin or user.password != password:
        return templates.TemplateResponse(
            request=request, name="admin_login.html", context={"error": "Неверные данные"}
        )
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="admin_session", value=email, httponly=True)
    return response

@router.get("/admin")
async def admin_dashboard(request: Request, admin: str = Depends(require_admin)):
    todos = await todo_db.get_all()
    users = await user_db.get_all()
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={"admin": admin, "todos": todos, "users": users}
    )

@router.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("admin_session")
    return response