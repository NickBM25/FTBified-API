import json
from pathlib import Path
from uuid import UUID
from fastapi import Depends, HTTPException, Response, APIRouter
from sqlmodel import Session, select
from models.stats import Stats
from models.player import Player
from utilities import snbt_utils, sftp_utils
from database import get_session

router = APIRouter(prefix="/api/v1/players")

@router.get("/", response_model=list[Player], status_code=200)
def read_players(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    if limit-skip <= 0:
        return []

    if limit-skip > 100:
        raise HTTPException(status_code=400, detail="Maximum limit exceeded. You can only request up to 100 players at a time.")

    return session.exec(select(Player).offset(skip).limit(limit)).all()


@router.post("/", response_model=Player, status_code=201)
def create_player(snbt, session: Session = Depends(get_session)):
    if not snbt or not snbt.strip():
        raise HTTPException(status_code=400, detail="SNBT não pode ser vazio")

    nbt = snbt_utils.parse_snbt_file(snbt)
    json_parsed = snbt_utils.snbt_to_json(nbt)
    player = Player(**json_parsed)

    existing = session.exec(select(Player).where(Player.player_id == player.player_id)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Player já existe")

    session.add(player)
    session.commit()
    return player

@router.get("/{player_id}", response_model=Player, status_code=200)
def read_player(player_id: UUID, session: Session = Depends(get_session)):
    player = session.exec(select(Player).where(Player.player_id == player_id)).first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player

@router.delete("/{player_id}")
def delete_player(player_id: UUID, session: Session = Depends(get_session)):
    player = session.exec(select(Player).where(Player.player_id == player_id)).first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    session.delete(player)
    session.commit()
    return Response(status_code=204)

@router.put("/{player_id}", response_model=Player, status_code=200)
def update_user(player_id: UUID, snbt: str, session: Session = Depends(get_session)):
    player = session.exec(select(Player).where(Player.player_id == player_id)).first()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if not snbt or not snbt.strip():
        raise HTTPException(status_code=400, detail="SNBT não pode ser vazio")

    nbt = snbt_utils.parse_snbt_file(snbt)
    json_parsed = snbt_utils.snbt_to_json(nbt)
    new_data = Player(**json_parsed)

    if new_data.player_id != player_id:
        raise HTTPException(status_code=400, detail="O UUID do SNBT não corresponde ao UUID da URL")

    new_data_dict = new_data.model_dump(exclude_unset=True, exclude={"player_id"})

    changes = {
        field: value
        for field, value in new_data_dict.items()
        if getattr(player, field) != value
    }

    if not changes:
        raise HTTPException(status_code=200, detail="Nenhuma alteração detectada")

    for field, value in changes.items():
        setattr(player, field, value)

    session.add(player)
    session.commit()
    session.refresh(player)
    return player

@router.put("/stats", response_model=Player, status_code=200)
def update_stats(path: str, session: Session = Depends(get_session)):
    uuid = Path(path).stem

    player = session.exec(select(Player).where(Player.player_id == uuid)).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    try:
        file = sftp_utils.getfile(path)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    j = json.loads(file)
    stats = Stats.model_validate(j | {"player_id": uuid})


    stats_dict = stats.model_dump(exclude={"player_id"})
    for field, value in stats_dict.items():
        setattr(player, field, value)
        session.add(player)

    session.commit()
    session.refresh(player)
    return player