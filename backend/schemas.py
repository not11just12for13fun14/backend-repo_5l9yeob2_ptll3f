from enum import Enum
from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class Status(str, Enum):
    new = "new"
    in_production = "in_production"
    completed = "completed"
    error = "error"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class JobBase(BaseModel):
    title: str = Field(..., description="Job ID or Title")
    assigned_to: str = Field(..., description="Assignee name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL for assignee")
    due_date: date
    priority: Priority = Priority.medium
    status: Status = Status.new


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    assigned_to: Optional[str] = None
    avatar_url: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None


class JobOut(JobBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }
