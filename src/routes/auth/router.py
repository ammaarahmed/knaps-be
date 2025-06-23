from fastapi import APIRouter
from typing import List, Optional
from ...models import User, Token
from ...storage import storage

router = APIRouter(prefix="/auth")


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}


# @router.post("/login", response_model=User)
# async def login(form_data: Annotated[User, Depends()]):
#     user = authenticate_user(fake_users_db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(status_code=401, detail="Incorrect username or password")
#     return {"access_token": user.username, "token_type": "bearer"}
