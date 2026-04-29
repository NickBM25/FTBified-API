from fastapi import FastAPI
from routers import players, teams

app = FastAPI()

@app.get("/api/v1/")
def root():
    return {"status": "online", "service": "FTBified API"}

app.include_router(players.router)
app.include_router(teams.router)
