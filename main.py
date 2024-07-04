from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from api.endpoints import adhar_router, pan_card_router, watshap_router



# Ensure all tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your routers
app.include_router(adhar_router, prefix="/api")
app.include_router(pan_card_router, prefix="/api")
app.include_router(watshap_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8003, reload=True, host='0.0.0.0')