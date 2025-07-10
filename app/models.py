# app/models.py

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Index

class PollOptionLink(SQLModel, table=True):
    """Tabla de enlace muchos-a-muchos Poll ⇄ Option"""
    __tablename__ = "polloption"
    
    poll_id: Optional[int] = Field(
        default=None, foreign_key="poll.id", primary_key=True
    )
    option_id: Optional[int] = Field(
        default=None, foreign_key="option.id", primary_key=True
    )
    
    # Índices para optimizar joins
    __table_args__ = (
        Index('idx_poll_option_poll_id', 'poll_id'),
        Index('idx_poll_option_option_id', 'option_id'),
    )

class Poll(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str
    theme: Optional[str] = Field(default=None)  # Theme to which the poll belongs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ends_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
    creator_id: Optional[int] = None

    # relaciones
    options: List["Option"] = Relationship(
        back_populates="polls",
        link_model=PollOptionLink
    )
    votes:   List["Vote"]   = Relationship(back_populates="poll")
    
    # Índices para consultas comunes
    __table_args__ = (
        Index('idx_poll_is_active', 'is_active'),
        Index('idx_poll_created_at', 'created_at'),
    )

class Option(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # relaciones
    polls: List[Poll]   = Relationship(
        back_populates="options",
        link_model=PollOptionLink
    )
    votes: List["Vote"] = Relationship(back_populates="option")

class Vote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    poll_id:   Optional[int] = Field(default=None, foreign_key="poll.id")
    option_id: Optional[int] = Field(default=None, foreign_key="option.id")
    user_id:   Optional[int] = Field(default=None)  # ya no es FK
    voted_at:  datetime      = Field(default_factory=datetime.utcnow)

    # relaciones
    poll:   Poll   = Relationship(back_populates="votes")
    option: Option = Relationship(back_populates="votes")
    
    # Índices para optimizar agregaciones
    __table_args__ = (
        Index('idx_vote_poll_id', 'poll_id'),
        Index('idx_vote_option_id', 'option_id'),
        Index('idx_vote_poll_option', 'poll_id', 'option_id'),
        Index('idx_vote_voted_at', 'voted_at'),
    )
