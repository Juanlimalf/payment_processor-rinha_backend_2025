from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings
from .interface.db_interface import DatabaseProtocol

STRING_CONNECTION_MYSQL = settings.DATABASE_URL


Base = declarative_base()


class PostgresDB(DatabaseProtocol):
    """Conexão com o banco de dados Mysql"""

    __instance = None
    __engine = create_engine(
        STRING_CONNECTION_MYSQL,
        pool_size=3,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=1000,
    )
    __session_factory = sessionmaker(bind=__engine)

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(PostgresDB, cls).__new__(cls)

        return cls.__instance

    def __init__(self):
        self.session: Union[Session, None] = None

    def get_engine(self):
        return self.__engine

    def __enter__(self):
        """abre a sessão com o banco de dados Mysql"""
        self.session = self.__session_factory()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """fecha a sessão com o banco de dados Mysql"""
        if self.session:
            self.session.close()

    def get_session(self):
        try:
            session = self.__session_factory()

            yield session
        finally:
            session.close()
