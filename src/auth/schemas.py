from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    name: str
    last_name: str = Field(alias="lastName")
    username: str
    email: str
    password: str

    model_config = {"populate_by_name": True}


class RegisterOut(BaseModel):
    id: int
    username: str
    email: str
    balance: float


class LoginIn(BaseModel):
    login: str
    password: str


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str


class ProfileOut(BaseModel):
    id: int
    name: str
    last_name: str
    username: str
    status: str
    balance: float
    datetime: str
