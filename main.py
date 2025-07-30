from fastapi import FastAPI
from config import app_settings
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from config import BASE_PATH, app_settings

from utils import lifespan
import modules


app = FastAPI(lifespan=lifespan.lifespan,
              version=app_settings.app_version, 
              title=app_settings.app_name)
app.include_router(modules.user.router)
app.include_router(modules.post.router)

# Allow frontend origin
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allow frontend origin
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def root():
    return {"message": "Up"}
