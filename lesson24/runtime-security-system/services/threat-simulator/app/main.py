from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title="Threat Simulator")

class ThreatSim(BaseModel):
    threat_type: str; description: str; executed: bool; timestamp: datetime

@app.post("/api/v1/simulate/shell-spawn", response_model=ThreatSim)
async def sim_shell():
    try:
        subprocess.run(["/bin/sh", "-c", "echo 'Test shell'"], capture_output=True, timeout=5)
        return ThreatSim(threat_type="SHELL_SPAWN", description="Shell spawned", executed=True, timestamp=datetime.utcnow())
    except Exception as e:
        return ThreatSim(threat_type="SHELL_SPAWN", description=str(e), executed=False, timestamp=datetime.utcnow())

@app.post("/api/v1/simulate/sensitive-file")
async def sim_file():
    try:
        open("/etc/shadow", "r")
    except: pass
    return ThreatSim(threat_type="FILE_ACCESS", description="Accessed /etc/shadow", executed=True, timestamp=datetime.utcnow())

@app.get("/health")
async def health(): return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn; uvicorn.run(app, host="0.0.0.0", port=8000)
