from datetime import timedelta
from uuid import UUID
from sqlmodel import SQLModel, Field
from pydantic import field_validator, AliasPath

class Player(SQLModel, table=True):
    __tablename__ = "players"
    minecraft_nickname: str = Field(validation_alias="player_name")
    discord_profile: str | None = None
    kills: int = Field(default=0, ge=0)
    deaths: int = Field(default=0, ge=0)
    play_time: timedelta = Field(default=timedelta(seconds=0))
    player_id: UUID = Field(validation_alias="id", primary_key=True)
    team_id: UUID | None = None
    player_role: str | None = Field(default=None, validation_alias="ranks")
    color: str = Field(validation_alias=AliasPath("properties", "ftbteams:color"))
    time_since_death: timedelta = Field(default=0)
    looted_chests: int = Field(default=0, ge=0)

    @field_validator("minecraft_nickname", "color")
    @classmethod
    def empty_str(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("não pode ser vazio")
        return v

    @field_validator("player_role", mode="before")
    @classmethod
    def extract_role(cls, v: dict) -> str | None:
        if not v:
            return None
        return next(iter(v.values()))

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("não pode ser vazio")
        if len(v) != 7 or not v.startswith("#"):
            raise ValueError("cor inválida, use o formato #RRGGBB")
        return v

class PlayerUpdate(SQLModel):
    minecraft_nickname: str | None = Field(default=None, validation_alias="player_name")
    player_id: UUID | None = Field(default=None, validation_alias="id")
    team_id: UUID | None = None
    player_role: str | None = Field(default=None, validation_alias="ranks")
    color: str | None = Field(default=None, validation_alias=AliasPath("properties", "ftbteams:color"))

    @field_validator("player_role", mode="before")
    @classmethod
    def extract_role(cls, v: dict) -> str | None:
        if not v:
            return None
        return next(iter(v.values()))

class PlayerStats(SQLModel):
    __tablename__ = "players"
    kills: int = Field(default=0, ge=0, validation_alias=AliasPath("stats", "minecraft:custom", "minecraft:mob_kills"))
    deaths: int = Field(default=0, ge=0, validation_alias=AliasPath("stats", "minecraft:custom", "minecraft:deaths"))
    play_time: timedelta = Field(default=0, validation_alias=AliasPath("stats", "minecraft:custom", "minecraft:play_time"))
    time_since_death: timedelta = Field(default=0, validation_alias=AliasPath("stats", "minecraft:custom", "minecraft:time_since_death"))
    looted_chests: int = Field(default=0, ge=0, validation_alias=AliasPath("stats", "minecraft:custom", "lootr:looted_stat"))
    player_id: UUID = Field(primary_key=True, foreign_key="players.player_id")

    @field_validator("play_time", "time_since_death", mode="before")
    @classmethod
    def convert_ticks_to_seconds(cls, t: int) -> timedelta:
        if not t:
            return timedelta(0)
        return timedelta(seconds=t/20)
