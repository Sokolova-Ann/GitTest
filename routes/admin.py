from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select, Session

from database.connection import get_session
from models.events import Event
from models.users import User

admin_router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")

ADMIN_COOKIE = "admin_session"

def require_admin(request: Request, session: Session = Depends(get_session)) -> User:
    email = request.cookies.get(ADMIN_COOKIE)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется вход в панель администратора"
        )
    statement = select(User).where(User.email == email, User.is_admin == True)
    admin = session.exec(statement).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return admin

@admin_router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={"error": None}
    )


@admin_router.post("/login")
async def login_submit(request: Request, session: Session = Depends(get_session)):
    form = await request.form()
    email = form.get("email", "")
    password = form.get("password", "")

    statement = select(User).where(User.email == email, User.is_admin == True)
    admin = session.exec(statement).first()

    if not admin or admin.password != password:
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={"error": "Неверный email или пароль"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key=ADMIN_COOKIE, value=admin.email, httponly=True)
    return response

@admin_router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    events = session.exec(select(Event)).all()
    users = session.exec(select(User)).all()
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "admin": admin,
            "events": events,
            "users": users
        }
    )

@admin_router.post("/event/{event_id}/delete")
async def delete_event_admin(
    event_id: int,
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    session.delete(event)
    session.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@admin_router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(ADMIN_COOKIE)
    return response