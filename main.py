import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from config import BASE_PATH, app_settings

from utils import lifespan
from modules.user import router as user_router
from modules.post import router as post_router
from modules.friends import router as friends_router
from modules.newsfeed import router as newsfeed_router

app = FastAPI(lifespan=lifespan.lifespan,
              version=app_settings.app_version, 
              title=app_settings.app_name)
app.include_router(user_router)
app.include_router(post_router)
app.include_router(friends_router)
app.include_router(newsfeed_router)
app.mount("/static", StaticFiles(directory="media"), name="static")


@app.get("/health")
async def root():
    return {"message": "Up"}
