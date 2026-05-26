"""Launch the FastAPI server (also initialises the DB)."""

import uvicorn
from backend import portfolio as port

if __name__ == "__main__":
    port.init_db()
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
