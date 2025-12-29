from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request, Response

from src.bot.dispatcher import get_bot, get_dispatcher
from src.config import settings

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request) -> Response:
    # Validate secret token
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    expected_secret = settings.telegram.webhook_secret.get_secret_value()

    if expected_secret and secret_token != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid secret token")

    # Parse update and feed to dispatcher
    bot = get_bot()
    dispatcher = get_dispatcher()

    update_data = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})

    await dispatcher.feed_update(bot, update)

    return Response(status_code=200)
