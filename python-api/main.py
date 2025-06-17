# main.py
from fastapi import FastAPI
import uvicorn
from app.core.config import settings
from typing import Dict

#routes
from app.api.v1.users import routes as users_router
from app.api.v1.openapi import router as integrations_router

# Create the FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI application with environment configuration",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include the users router
app.include_router(users_router.router, prefix=settings.API_V1_STR + "/users", tags=["users"])

#include the OpenApi router
app.include_router(
    integrations_router.router,
    prefix=settings.API_V1_STR + "/openapi",
    tags=["OpenRouter"]
)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Hello, world!"}

@app.get("/env", 
    response_model=Dict[str, str | bool],
    summary="Get Environment Information",
    description="Returns the current environment configuration including environment type, debug mode, and version information.",
    tags=["Environment"]
)
def get_environment_info():
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_version": settings.API_V1_STR
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
