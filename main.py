from fastapi import FastAPI
from config import app_settings
from utils import lifespan


app = FastAPI(lifespan=lifespan.lifespan,
              version=app_settings.app_version, 
              title=app_settings.app_name)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
