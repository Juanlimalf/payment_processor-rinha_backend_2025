from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api import app_router
from api.config.postgres import Base, PostgresDB


@asynccontextmanager
async def start_db(app: FastAPI):
    print("Starting database")
    connection = PostgresDB()

    engine = connection.get_engine()
    Base.metadata.create_all(engine)
    yield

    print("Closing database")
    engine.dispose()


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
    return {"message": "Welcome to the app API"}


if __name__ == "__main__":
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=9999,
        workers=1,
        access_log=False,
        server_header=False,  # Removendo server header
        date_header=False,
    )

    server = uvicorn.Server(config)

    server.run()
