from pathlib import Path
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
PUBLIC_DIR = REPO_ROOT / "dist" / "public"


def mount_static(app: FastAPI) -> None:
    if not PUBLIC_DIR.exists():
        raise RuntimeError(
            f"Could not find the build directory: {PUBLIC_DIR}. Run 'npm run build' first."
        )
    app.mount(
        "/",
        StaticFiles(directory=str(PUBLIC_DIR), html=True),
        name="static",
    )


