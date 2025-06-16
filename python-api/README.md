# FastAPI Project

## Initial Startup
```
uv venv
source .venv/bin/activate
uv sync #syncs pyproject.toml, uv.lock files and local env
uvicorn main:app --reload
```

## Adding/Removing Packages
```
uv add [PACKAGE]
uv remove [PACKAGE]
```

## API Documentation
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc