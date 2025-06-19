from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware


from .database import init_db
from .config import settings
import logging, yaml

from .routes.products.router import router as products_router
from .routes.sell_ins.router import router as sell_ins_router
from .routes.sell_throughs.router import router as sell_throughs_router
from .routes.analytics.router import router as analytics_router

app = FastAPI()

# with open('python_server/logging.yaml') as f:
#     cfg = yaml.safe_load(f)
# logging.config.dictConfig(cfg)

logger = logging.getLogger('uvicorn.error')

# TODO add for porduction env 
# app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com", "127.0.0.1"])
# # CORS configuration

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(sell_ins_router)
app.include_router(sell_throughs_router)
app.include_router(analytics_router)

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def main():
    return {"message": "Application alive"}

