import asyncio

from config import AsyncPostgresDB
from services.worker import worker


async def main(connection: AsyncPostgresDB):
    try:
        print("iniciando o worker...")
        await worker(connection)
    except Exception as e:
        print(e)
    finally:
        await connection.close()
        print("worker finalizado")


if __name__ == "__main__":
    conn = AsyncPostgresDB()
    loop = asyncio.new_event_loop()

    loop.run_until_complete(main(conn))
