from fastapi import FastAPI
from config import app_settings
from utils import lifespan
import modules


app = FastAPI(lifespan=lifespan.lifespan,
              version=app_settings.app_version, 
              title=app_settings.app_name)
app.include_router(modules.user.router)
app.include_router(modules.post.router)


@app.get("/health")
async def root():
    return {"message": "Up"}
