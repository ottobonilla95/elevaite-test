from dotenv import load_dotenv
import os

if not os.getenv("KUBERNETES_SERVICE_HOST"):
    load_dotenv()
# Initialize Redis database connection whenever its created TBD

session_status = {"superuser@iopex.com": "Testing..."}

async def update_status(user_if: str, status: str):
    """Update the status for a specific session."""
    session_status[user_if] = status

async def get_status(uid: str) -> str:
    """Get the status for a specific session."""
    return session_status.get(uid, "Status not found...")




