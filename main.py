import model
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import Base, engine
from api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(title="Apex Hunter", lifespan=lifespan)

app.include_router(router)
