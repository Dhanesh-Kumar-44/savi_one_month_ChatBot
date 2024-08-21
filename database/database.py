from sqlmodel import create_engine, SQLModel, Session

DataBase_URL = 'sqlite:///db.sqlite'

engine = create_engine(DataBase_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session