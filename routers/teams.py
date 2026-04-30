from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from constants import TEAM_BASE_PATH
from database import get_session
from dependencies import get_sftp_file, parse_snbt, get_team_from_db, apply_changes, get_player_from_db
from models.player import Player
from models.team import Team

router = APIRouter(prefix="/api/v1/teams")

@router.post("/", response_model=Team, status_code=201)
def create_team(
        team_id: UUID,
        session: Session = Depends(get_session)
):
    path = f'{TEAM_BASE_PATH}/{team_id}'
    snbt = get_sftp_file(path)
    data = parse_snbt(snbt)
    team = Team.model_validate(data)

    existing = session.get(Team, team.team_id)
    if existing:
        raise HTTPException(status_code=409, detail="Team already exists")

    session.add(team)
    session.commit()
    session.refresh(team)

    #update_team_members(team.team_id)

    return team

@router.get("/", response_model=list[Team], status_code=200)
def read_teams(
        offset: int = 0,
        limit: int = 100,
        session: Session = Depends(get_session)
):
    if offset < 0 or limit <= 0:
        return []

    if limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum limit exceeded. You can only request up to 100 teams at a time."
        )

    return session.exec(select(Team).offset(offset).limit(limit)).all()

@router.get("/{team_id}", response_model=Team, status_code=200)
def read_team(
        team_id: UUID,
        session: Session = Depends(get_session)
):
    team = get_team_from_db(team_id, session)
    return team

@router.patch("/{team_id}", response_model=Team, status_code=200)
def update_team(
        team_id: UUID,
        session: Session = Depends(get_session)
):
    team = get_team_from_db(team_id, session)

    path = f'{TEAM_BASE_PATH}/{team_id}'
    snbt = get_sftp_file(path)
    data = parse_snbt(snbt)
    team_update = Team.model_validate(data)

    if team_update.team_id != team.team_id:
        raise HTTPException(
            status_code=400,
            detail="Team UUID from update request is not the same UUID from requested Team"
        )

    team_update_dict = team_update.model_dump(
        exclude={"team_id"},
        exclude_none=True
    )

    if not apply_changes(team, team_update_dict):
        return team

    team.last_updated = datetime.now()
    session.add(team)
    session.commit()
    session.refresh(team)
    return team

@router.patch("/{team_id}/members", response_model=Team, status_code=200)
def update_team_members(
        team_id: UUID,
        session: Session = Depends(get_session)
):
    team = get_team_from_db(team_id, session) #get current team

    #get team new data
    path = f'{TEAM_BASE_PATH}/{team_id}.snbt'
    snbt = get_sftp_file(path)
    data = parse_snbt(snbt)
    team_update = Team.model_validate(data)

    #check if the update request is not deprecated
    update_timestamp = datetime.now(timezone.utc)
    if team.last_updated > update_timestamp:
        raise HTTPException (
            status_code=409,
            detail="Update request is older than the last update"
        )

    #get all current players from team
    current_players = session.exec(
        select(Player).where(Player.team_id == team_id)
    ).all()

    #filter necessary data
    updated_ids = set(team_update.members)
    current_ids = {p.player_id for p in current_players}
    players_map = {p.player_id: p for p in current_players}

    #remove and player if not in team anymore
    for member_id in current_ids - updated_ids:
        player = players_map[member_id]
        player.team_id = None
        player.player_role = "Owner" #Owner is the role default value for non-team players
        session.add(player)

    #add new members and update roles
    for member_id in updated_ids:
        updated = False
        try:
            player = players_map.get(member_id) or get_player_from_db(member_id, session)
            if player.team_id != team.team_id:
                player.team_id = team.team_id
                updated = True
            if player.player_role != team_update.members[member_id]:
                player.player_role = team_update.members[member_id]
                updated = True
            if updated:
                session.add(player)
        except HTTPException:
            raise HTTPException(status_code=404, detail=f"Player {member_id} not found in database")

    team.last_updated = update_timestamp
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


@router.delete("/{team_id}", response_model=Team, status_code=204)
def delete_team(team_id: UUID, session: Session = Depends(get_session)):
    team = get_team_from_db(team_id, session)

    session.delete(team)
    session.commit()
    return
