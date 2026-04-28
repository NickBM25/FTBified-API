from datetime import timedelta
from uuid import UUID
from pydantic import AliasPath, field_validator
from sqlmodel import Field, SQLModel


class Stats(SQLModel, table=True):
    __tablename__ = "players"
    kills: int = Field(default=0, ge=0, validation_alias=AliasPath("stats", "minecraft:custom", "minecraft:mob_kills"))
    deaths: int = Field(default=0, ge=0, validation_alias=AliasPath("stats", "minecraft:custom", "minecraft:deaths"))
    playtime: timedelta = Field(default=0, validation_alias=AliasPath("stats", "minecraft:custom", "minecraft:play_time"))
    time_since_death: timedelta = Field(default=0, validation_alias=AliasPath("stats", "minecraft:custom", "minecraft:time_since_death"))
    looted_chests: int | None = Field(default=0, ge=0, validation_alias=AliasPath("stats", "minecraft:custom", "lootr:looted_stat"))
    player_id: UUID = Field(primary_key=True, foreign_key="players.player_id")

    @field_validator("playtime", "time_since_death", mode="before")
    @classmethod
    def convert_ticks_to_seconds(cls, t: int) -> timedelta:
        return timedelta(seconds=t/20)
