from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

class PollOptionLink(SQLModel, table=True):
    poll_id: Optional[int] = Field(
        default=None, foreign_key="poll.id", primary_key=True
    )
    option_id: Optional[int] = Field(
        default=None, foreign_key="option.id", primary_key=True
    )

class Poll(SQLModel, table=True):
    __tablename__ = "poll"
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    options: List["Option"] = Relationship(
        back_populates="poll", link_model=PollOptionLink
    )

class Option(SQLModel, table=True):
    __tablename__ = "option"
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str

    poll: Optional[Poll] = Relationship(
        back_populates="options", link_model=PollOptionLink
    )

class Vote(SQLModel, table=True):
    __tablename__ = "vote"
    id: Optional[int] = Field(default=None, primary_key=True)
    poll_id: int = Field(foreign_key="poll.id")
    option_id: int = Field(foreign_key="option.id")
    voted_at: datetime = Field(default_factory=datetime.utcnow)