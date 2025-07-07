from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, select
from pydantic import validator
from sqlalchemy.ext.asyncio import AsyncSession

class PollOptionLink(SQLModel, table=True):
    """Link table between Poll and Option entities."""
    poll_id: Optional[int] = Field(
        default=None, foreign_key="poll.id", primary_key=True
    )
    option_id: Optional[int] = Field(
        default=None, foreign_key="option.id", primary_key=True
    )

class User(SQLModel, table=True):
    """User model for authentication and vote tracking."""
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    votes: List["Vote"] = Relationship(back_populates="user")
    polls: List["Poll"] = Relationship(back_populates="creator")

class Poll(SQLModel, table=True):
    """Poll model containing a question and options."""
    __tablename__ = "poll"
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ends_at: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    creator_id: Optional[int] = Field(default=None, foreign_key="user.id")

    options: List["Option"] = Relationship(
        back_populates="polls", link_model=PollOptionLink
    )
    votes: List["Vote"] = Relationship(back_populates="poll")
    creator: Optional[User] = Relationship(back_populates="polls")

    @validator("ends_at")
    def validate_end_date(cls, ends_at, values):
        """Ensure end date is after creation date."""
        if ends_at and values.get("created_at") and ends_at <= values["created_at"]:
            raise ValueError("End date must be after creation date")
        return ends_at

    async def get_results(self, session: AsyncSession) -> Dict[str, int]:
        """Get vote counts for each option."""
        results = {}
        for option in self.options:
            count_query = select([Vote]).where(
                Vote.poll_id == self.id, 
                Vote.option_id == option.id
            )
            result = await session.execute(count_query)
            count = len(result.all())
            results[option.text] = count
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert poll to dictionary."""
        return {
            "id": self.id,
            "question": self.question,
            "created_at": self.created_at.isoformat(),
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
            "is_active": self.is_active,
            "options": [option.to_dict() for option in self.options]
        }

class Option(SQLModel, table=True):
    """Option model for poll choices."""
    __tablename__ = "option"
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    polls: List[Poll] = Relationship(
        back_populates="options", link_model=PollOptionLink
    )
    votes: List["Vote"] = Relationship(back_populates="option")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert option to dictionary."""
        return {
            "id": self.id,
            "text": self.text
        }

class Vote(SQLModel, table=True):
    """Vote model for recording user votes."""
    __tablename__ = "vote"
    id: Optional[int] = Field(default=None, primary_key=True)
    poll_id: int = Field(foreign_key="poll.id", index=True)
    option_id: int = Field(foreign_key="option.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    voted_at: datetime = Field(default_factory=datetime.utcnow)

    poll: Poll = Relationship(back_populates="votes")
    option: Option = Relationship(back_populates="votes")
    user: User = Relationship(back_populates="votes")
    
    @validator("option_id")
    def validate_option(cls, option_id, values):
        """Ensure option belongs to the poll."""
        # Note: This would need more complex validation in actual code
        return option_id
    
    @classmethod
    async def has_user_voted(cls, session: AsyncSession, user_id: int, poll_id: int) -> bool:
        """Check if a user has already voted on a poll."""
        query = select(Vote).where(Vote.user_id == user_id, Vote.poll_id == poll_id)
        result = await session.execute(query)
        return result.first() is not None