from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import articles, categories, health
from src.db.engine import engine
from src.db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Web Crawler CMS", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(articles.router)
app.include_router(categories.router)


@app.post("/api/crawl")
def trigger_crawl():
    from src.db.engine import get_session
    from src.scheduler.job_manager import crawl_all

    with get_session() as db:
        result = crawl_all(db)
    return result
