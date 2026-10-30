from sqlmodel import SQLModel, Session, create_engine, select
from models.events import Event
from models.users import User

database_file = "planner.db"
database_connection_string = f"sqlite:///{database_file}"
connect_args = {"check_same_thread": False}

engine_url = create_engine(
    database_connection_string,
    echo=True,
    connect_args=connect_args
)


def conn():
    SQLModel.metadata.create_all(engine_url)
    create_default_admin()


def get_session():
    with Session(engine_url) as session:
        yield session


def create_default_admin():
    with Session(engine_url) as session:
        statement = select(User).where(User.email == "admin@planner.local")
        existing = session.exec(statement).first()
        if not existing:
            admin = User(
                email="admin@planner.local",
                password="admin123",
                is_admin=True,
                events=[]
            )
            session.add(admin)
            session.commit()
            print(">>> Создан администратор: admin@planner.local / admin123")