from contextlib import asynccontextmanager
from typing import AsyncGenerator, Union

import asyncpg

from .settings import settings


class AsyncPostgresDB:
    """Conexão com o banco de dados Mysql"""

    __session_pool: Union[asyncpg.Pool, None] = None
    __dsn = settings.DATABASE_URL

    async def init_pool(self, min_size=1, max_size=10):
        if self.__session_pool is None:
            self.__session_pool = await asyncpg.create_pool(self.__dsn, min_size=min_size, max_size=max_size)

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        if self.__session_pool is None:
            await self.init_pool()

        async with self.__session_pool.acquire() as conn:
            yield conn

    async def close(self):
        if self.__session_pool:
            await self.__session_pool.close()
            self.__session_pool = None
