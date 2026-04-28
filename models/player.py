from datetime import timedelta
from uuid import UUID
from sqlmodel import SQLModel, Field
from pydantic import field_validator, AliasPath
from utilities import snbt_utils, file_utils


class Player(SQLModel, table=True):
    __tablename__ = "players"
    nickname: str = Field(validation_alias="player_name")
    discord: str | None = None
    kills: int = Field(default=0, ge=0)
    deaths: int = Field(default=0, ge=0)
    playtime: timedelta | None = Field(default=timedelta(seconds=0))
    player_id: UUID = Field(validation_alias="id", primary_key=True)
    team_id: UUID | None = None
    role: str | None = Field(default=None, validation_alias="ranks")
    color: str = Field(validation_alias=AliasPath("properties", "ftbteams:color"))

    @field_validator("nickname", "color")
    @classmethod
    def empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("não pode ser vazio")
        return v

    @field_validator("role", mode="before")
    @classmethod
    def extract_role(cls, v: dict) -> str | None:
        if not v:
            return None
        return next(iter(v.values()))