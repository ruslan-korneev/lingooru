"""Shared constants for Telegram bot handlers."""

# Menu button texts to ignore as word input (all translations)
MENU_BUTTONS: set[str] = {"📋 Меню", "📋 Menu", "📋 메뉴"}
LEARN_BUTTONS: set[str] = {"📚 Учить", "📚 Learn", "📚 배우기"}
REVIEW_BUTTONS: set[str] = {"🔄 Повторять", "🔄 Review", "🔄 복습"}

# Language pair display names for UI
PAIR_DISPLAY: dict[str, str] = {
    "en_ru": "EN → RU",
    "ko_ru": "KO → RU",
}
