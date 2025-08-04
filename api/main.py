from contextlib import asynccontextmanager

from fastapi import FastAPI

from config.postgresDB import AsyncPostgresDB
from router.router import router as app_router

conn = AsyncPostgresDB()


@asynccontextmanager
async def start_db(app: FastAPI):
    print("Starting database")
    await conn.init_pool()
    await conn.create_table()

    yield
    await conn.close()
    print("Closing database")


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    title="Payment Processor API",
    description="API for processing payments in the Rinha de Backend",
    lifespan=start_db,
)

app.include_router(app_router)


@app.get("/")
async def root():
    return {"message": "Benvindo a Api do Rinha de Backend 2025 - Payment Processor by Juan Lima"}


# if __name__ == "__main__":
#     config = uvicorn.Config(
#         app,
#         host="0.0.0.0",
#         port=8000,
#         workers=2,
#         access_log=False,
#         server_header=False,
#         date_header=False,
#     )

#     server = uvicorn.Server(config)

#     server.run()
