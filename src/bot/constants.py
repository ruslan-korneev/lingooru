"""Shared constants for Telegram bot handlers."""

from typing import NamedTuple


class Greeting(NamedTuple):
    """Greeting in a foreign language with transcription."""

    language_code: str
    flag: str
    native_text: str
    transcription: str


GREETINGS: tuple[Greeting, ...] = (
    Greeting("en", "🇬🇧", "Hello!", "Hello!"),
    Greeting("ko", "🇰🇷", "안녕하세요!", "Annyeonghaseyo!"),
    Greeting("ru", "🇷🇺", "Привет!", "Privet!"),
    Greeting("ja", "🇯🇵", "こんにちは!", "Konnichiwa!"),
    Greeting("es", "🇪🇸", "¡Hola!", "Oh-la!"),
    Greeting("fr", "🇫🇷", "Bonjour!", "Bon-zhoor!"),
    Greeting("de", "🇩🇪", "Hallo!", "Hallo!"),
    Greeting("it", "🇮🇹", "Ciao!", "Chow!"),
    Greeting("zh", "🇨🇳", "你好!", "Ni hao!"),
    Greeting("ar", "🇸🇦", "مرحبا!", "Marhaba!"),
    Greeting("hi", "🇮🇳", "नमस्ते!", "Namaste!"),
    Greeting("pt", "🇧🇷", "Olá!", "Ola!"),
    Greeting("nl", "🇳🇱", "Hallo!", "Hallo!"),
    Greeting("tr", "🇹🇷", "Merhaba!", "Merhaba!"),
    Greeting("pl", "🇵🇱", "Cześć!", "Cheshch!"),
)


# Menu button texts to ignore as word input (all translations)
MENU_BUTTONS: set[str] = {"📋 Меню", "📋 Menu", "📋 메뉴"}
LEARN_BUTTONS: set[str] = {"📚 Учить", "📚 Learn", "📚 배우기"}
REVIEW_BUTTONS: set[str] = {"🔄 Повторять", "🔄 Review", "🔄 복습"}

# Language pair display names for UI
PAIR_DISPLAY: dict[str, str] = {
    "en_ru": "EN → RU",
    "ko_ru": "KO → RU",
}
