from fastapi import FastAPI
from MusicManager.FileManager import scan

app = FastAPI()

@app.get("/tracks")
def get_tracks():
    return scan('./Music')
