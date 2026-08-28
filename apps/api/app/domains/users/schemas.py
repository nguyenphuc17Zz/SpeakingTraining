from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    display_name: str = "Learner"
    timezone: str = "Asia/Tokyo"
    locale: str = "ja-JP"


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    display_name: str | None = None
    timezone: str | None = None
    locale: str | None = None


class UserRead(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
