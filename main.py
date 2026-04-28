from fastapi import FastAPI
from routers import players, teams

app = FastAPI()

app.include_router(players.router)
app.include_router(teams.router)
