from contextlib import asynccontextmanager
from typing import AsyncGenerator, Union

import asyncpg

from .settings import settings


class AsyncPostgresDB:
    """Conexão com o banco de dados Mysql"""

    __instance = None
    __session_pool: Union[asyncpg.Pool, None] = None
    __dsn = settings.DATABASE_URL

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(AsyncPostgresDB, cls).__new__(cls)

        return cls.__instance

    async def init_pool(self, min_size=1, max_size=10):
        if self.__session_pool is None:
            self.__session_pool = await asyncpg.create_pool(self.__dsn, min_size=min_size, max_size=max_size)

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if self.__session_pool is None:
            await self.init_pool()

        conn = await self.__session_pool.acquire()
        try:
            yield conn
        finally:
            await self.__session_pool.release(conn)

    async def close(self):
        if self.__session_pool:
            await self.__session_pool.close()
            self.__session_pool = None
