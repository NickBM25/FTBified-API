from fastapi import HTTPException
from sqlmodel import Session, select

from models.player import Player
from models.team import Team
from utilities import sftp_utils, snbt_utils


def get_sftp_file(path : str) -> str:
    try:
        file = sftp_utils.getfile(path)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not file or not file.strip():
        raise HTTPException(status_code=400, detail="SNBT não pode ser vazio")
    return file

def parse_snbt(snbt: str) -> dict:
    nbt = snbt_utils.parse_snbt_file(snbt)
    json = snbt_utils.snbt_to_json(nbt)
    return json

def apply_changes(existing, updated_dict: dict) -> bool:
    changes = {
        field: value
        for field, value in updated_dict.items()
        if hasattr(existing, field) and getattr(existing, field) != value
    }

    if not changes:
        return False

    for field, value in changes.items():
        setattr(existing, field, value)

    return True

def get_player_from_db(player_id: str, session: Session) -> Player:
    player = session.exec(select(Player).where(Player.player_id == player_id)).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

def get_team_from_db(team_id: str, session: Session) -> Team:
    team = session.exec(select(Team).where(Team.team_id == team_id)).first()
    if not team:
        raise HTTPException(status_code=404, detail="Player not found")
    return team
