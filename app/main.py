from app.api.main import app

__all__ = ["app"]


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
