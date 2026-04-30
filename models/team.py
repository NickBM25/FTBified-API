from datetime import datetime, timezone
from uuid import UUID
from sqlmodel import SQLModel, Field
from pydantic import field_validator, AliasPath

class Team(SQLModel, table=True):
    __tablename__ = "teams"
    name: str = Field(validation_alias=AliasPath("properties", "ftbteams:display_name"))
    color: str = Field(validation_alias=AliasPath("properties", "ftbteams:color"))
    members: dict[UUID, str] = Field(validation_alias="ranks")
    discord_role: str | None = None
    team_id: UUID = Field(validation_alias="id", primary_key=True)
    last_updated: datetime = Field(default_factory=datetime.now(timezone.utc))

    @field_validator("name", "color")
    @classmethod
    def empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("não pode ser vazio")
        return v