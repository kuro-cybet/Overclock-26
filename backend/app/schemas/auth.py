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


class GoogleLoginRequest(BaseModel):
    """The ID token handed back by Google Identity Services."""

    credential: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary
    # Set when a system_admin is previewing another role's portal.
    impersonated_by: Optional[str] = None
    impersonated_by_name: Optional[str] = None


class ImpersonateRequest(BaseModel):
    """A system_admin asks for a scoped token for another portal role."""

    role: Optional[str] = None
    user_id: Optional[str] = None
