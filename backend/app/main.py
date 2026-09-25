from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .api import craftsmen, messages, audio, archives, materials

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="弓道纪要 API",
    description="传统弓箭制作工艺传承平台后端API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(craftsmen.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(archives.router, prefix="/api")
app.include_router(materials.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "弓道纪要 API",
        "version": "1.0.0",
        "description": "传统弓箭制作工艺传承平台",
        "endpoints": {
            "craftsmen": "/api/craftsmen",
            "messages": "/api/messages",
            "audio": "/api/audio",
            "archives": "/api/archives",
            "materials": "/api/materials"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
