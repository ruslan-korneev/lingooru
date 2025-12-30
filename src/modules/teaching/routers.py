from fastapi import APIRouter

router = APIRouter(prefix="/teaching", tags=["teaching"])

# API endpoints will be added in future phases if needed.
# Currently, all teaching functionality is exposed via Telegram bot handlers.
