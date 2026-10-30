from typing import Optional
from pydantic import BaseModel, EmailStr

class UserSummary(BaseModel):
    id: str
    email: str
    name: str
    role: str
    sub_role: Optional[str] = None
    department: Optional[str] = None
    building_id: Optional[str] = None
    floor_id: Optional[str] = None

class DemoAccountResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    sub_role: Optional[str] = None
    department: Optional[str] = None
    password: str = "password123"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary
