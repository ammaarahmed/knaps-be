import json
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from pydantic import BaseModel
from typing import List
from .database import get_async_session
from .db_models import User
from src import storage 

auth_scheme = HTTPBearer()

# TODO move this to read from env 
KEYCLOAK_CLIENT=  "fastapi-api"
KEYCLOAK_SERVER= "http://localhost:8080"
REALM= "ammaar"

class TokenData(BaseModel):
    sub: str
    realm_access: dict
    groups: List[str] = []


async def get_current_user(token=Depends(auth_scheme)):
    credentials = token.credentials
    # Fetch JWKS from: {KEYCLOAK_SERVER}/realms/{REALM}/protocol/openid-connect/certs
    with open('keycloak-values.json', 'r') as f:
        public_keys = json.load(f)
    payload = jwt.decode(
        credentials,
        public_keys["keys"],
        algorithms=["RS256"],
        audience=KEYCLOAK_CLIENT,
    )
    data = TokenData(**payload)

    # Upsert into Postgres
    async with get_async_session() as session:
        user = await storage.get_user(data.sub)
        if not user:
            user = await storage.create_user(User(keycloak_id=data.sub, email=payload.get("email")))
            await session.commit()
            await session.refresh(user)
    return user, data
