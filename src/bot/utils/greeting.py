"""Greeting utilities for welcome messages."""

import random

from src.bot.constants import GREETINGS, Greeting


def get_random_greeting() -> Greeting:
    """Get a random greeting from available languages."""
    return random.choice(GREETINGS)  # noqa: S311


def format_greeting(greeting: Greeting) -> str:
    """Format greeting for display: '{flag} {text}\n({transcription})'."""
    return f"{greeting.flag} {greeting.native_text}\n({greeting.transcription})"
