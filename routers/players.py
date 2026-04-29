import json
from uuid import UUID
from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from constants import PLAYER_BASE_PATH, STATS_BASE_PATH
from models.player import Player, PlayerStats, PlayerUpdate
from database import get_session
from dependencies import get_player_from_db, get_sftp_file, parse_snbt, apply_changes

router = APIRouter(prefix="/api/v1/players")

@router.post("/", response_model=Player, status_code=201)
def create_player(
    player_id: UUID,
    session: Session = Depends(get_session)
):
    path = f"{PLAYER_BASE_PATH}/{player_id}.snbt"
    snbt = get_sftp_file(path)

    data = parse_snbt(snbt)
    player = Player.model_validate(data)

    existing = session.get(Player, player.player_id)
    if existing:
        raise HTTPException(status_code=409, detail="Player already exists")

    session.add(player)
    session.commit()
    session.refresh(player)

    update_stats(player.player_id, session)

    return player

@router.get("/", response_model=list[Player], status_code=200)
def read_players(
    offset: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    if limit <= 0 or offset < 0:
        return []

    if limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum limit exceeded. You can only request up to 100 players at a time."
        )

    return session.exec(select(Player).offset(offset).limit(limit)).all()

@router.get("/{player_id}", response_model=Player, status_code=200)
def read_player(
    player_id: UUID,
    session: Session = Depends(get_session)
):
    player = get_player_from_db(player_id, session)
    return player


@router.patch("/{player_id}", response_model=Player, status_code=200)
def update_player(
    player_id: UUID,
    session: Session = Depends(get_session)
):
    path = f"{PLAYER_BASE_PATH}/{player_id}.snbt"

    player = get_player_from_db(player_id, session)

    snbt = get_sftp_file(path)
    data = parse_snbt(snbt)
    player_update = PlayerUpdate.model_validate(data)


    if player_update.player_id != player_id:
        raise HTTPException(
            status_code=400,
            detail="Player UUID from update request is not the same UUID from requested player"
        )

    player_update_dict = player_update.model_dump(
        exclude={"player_id"},
        exclude_none=True
    )

    if not apply_changes(player, player_update_dict):
        return player

    session.add(player)
    session.commit()
    session.refresh(player)
    return player

@router.patch("/{player_id}/stats", response_model=Player, status_code=200)
def update_stats(
        player_id: UUID,
        session: Session = Depends(get_session)
):
    path = f"{STATS_BASE_PATH}/{player_id}.json"

    player = get_player_from_db(player_id, session)

    file = get_sftp_file(path)
    j = json.loads(file)
    stats = PlayerStats.model_validate(j | {"player_id": player_id})

    stats_dict = stats.model_dump(
        exclude={"player_id"},
        exclude_none=True
    )

    if not apply_changes(player, stats_dict):
        return player

    session.add(player)
    session.commit()
    session.refresh(player)
    return player

@router.delete("/{player_id}", status_code=204)
def delete_player(
    player_id: UUID,
    session: Session = Depends(get_session)
):
    player = get_player_from_db(player_id, session)

    session.delete(player)
    session.commit()
    return