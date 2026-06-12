from datetime import datetime
from pydantic import BaseModel
from app.models.user import UserRole, SeniorityLevel


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: UserRole
    seniority_level: SeniorityLevel
    desk: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
