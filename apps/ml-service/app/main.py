from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.ws_translate import router as ws_router
from app.routes.info import router as info_router

app = FastAPI(title="ISL Translator ML Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your web app's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(info_router)
app.include_router(ws_router)


@app.get("/")
def root():
    return {"service": "isl-ml-service", "status": "running"}
