"""
Base models following DRY principle - common patterns used across the system.
Extends existing domain entity patterns from backend.domain.entities.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC


class BaseEntity(BaseModel):
    """Base entity following existing domain patterns (DRY)"""
    id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True


class BaseValueObject(BaseModel):
    """Base value object for immutable data (DRY)"""
    
    class Config:
        frozen = True
        arbitrary_types_allowed = True


class TimestampedEntity(BaseEntity):
    """Entity with timestamps - reuses existing pattern (DRY)"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def update_timestamp(self):
        """Update the timestamp when entity is modified"""
        self.updated_at = datetime.now()


class ProcessingEntity(TimestampedEntity):
    """Base for processing entities - follows existing intelligence patterns"""
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None
    requires_human_review: bool = False