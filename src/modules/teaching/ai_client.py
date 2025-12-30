"""AI client for assignment generation and checking."""

import json
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger

from src.config import settings
from src.modules.teaching.enums import AssignmentType

# Score thresholds for feedback
SCORE_EXCELLENT = 90
SCORE_GOOD = 70
SCORE_FAIR = 50

# Voice rating thresholds
VOICE_EXCELLENT = 4.5
VOICE_GOOD = 4
VOICE_FAIR = 3
VOICE_CORRECT_THRESHOLD = 4


@dataclass
class GeneratedAssignment:
    """Result from AI assignment generation."""

    title: str
    description: str
    content: dict[str, Any]


@dataclass
class AICheckResult:
    """Result from AI assignment checking."""

    score: int  # 0-100
    feedback: str
    detailed_results: list[dict[str, Any]]


# Prompt templates
GENERATION_PROMPT_TEXT = """You are a language teacher creating a {assignment_type} assignment.
The student is learning {target_language} from {source_language}.
Topic: {topic}
Difficulty: {difficulty}
Create {question_count} questions.

For TEXT assignments respond in this JSON format:
{{
    "title": "Assignment title (short)",
    "description": "Brief description",
    "questions": [
        {{"id": "q1", "text": "Question text", "expected": "Expected answer or null if open-ended"}}
    ]
}}

For MULTIPLE_CHOICE assignments respond in this JSON format:
{{
    "title": "Assignment title (short)",
    "description": "Brief description",
    "questions": [
        {{
            "id": "q1",
            "text": "Question text",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_index": 0
        }}
    ]
}}

For VOICE assignments respond in this JSON format:
{{
    "title": "Assignment title (short)",
    "description": "Brief description",
    "words": [
        {{"id": "w1", "text": "Word to pronounce", "phonetic": "IPA transcription or null"}}
    ]
}}

Create content in {target_language} for the student to learn.
"""

CHECK_PROMPT_TEXT = """You are a language teacher checking student answers.
The student is learning {target_language} from {source_language}.

Assignment questions:
{questions}

Student answers:
{answers}

For each answer, evaluate correctness and provide helpful feedback.
Respond in JSON format:
{{
    "score": <0-100 overall score>,
    "feedback": "Overall feedback in Russian (2-3 sentences)",
    "detailed_results": [
        {{"question_id": "q1", "correct": true/false, "feedback": "Feedback for this answer in Russian"}}
    ]
}}

Be encouraging but honest. Give specific tips for improvement.
"""


class TeachingAIClient:
    """Client for AI-powered assignment generation and checking."""

    CHAT_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self) -> None:
        api_key = settings.openai.api_key.get_secret_value()
        self._client = httpx.AsyncClient(
            timeout=settings.openai.timeout_seconds,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def generate_assignment(
        self,
        topic: str,
        assignment_type: AssignmentType,
        language_pair: str,
        difficulty: str = "medium",
        question_count: int = 5,
    ) -> GeneratedAssignment:
        """Generate assignment content using GPT-4o."""
        # Parse language pair (e.g., "en_ru" -> "English", "Russian")
        source_lang, target_lang = self._parse_language_pair(language_pair)

        prompt = GENERATION_PROMPT_TEXT.format(
            assignment_type=assignment_type.value,
            target_language=target_lang,
            source_language=source_lang,
            topic=topic,
            difficulty=difficulty,
            question_count=question_count,
        )

        try:
            response = await self._client.post(
                self.CHAT_URL,
                json={
                    "model": settings.openai.gpt_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            data = json.loads(content)

            return GeneratedAssignment(
                title=data.get("title", f"Assignment: {topic}"),
                description=data.get("description", ""),
                content=self._extract_content(data, assignment_type),
            )

        except httpx.HTTPError as e:
            logger.error(f"GPT-4o API error during generation: {e}")
            raise
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse GPT-4o response: {e}")
            raise

    async def check_text_assignment(
        self,
        questions: list[dict[str, Any]],
        answers: list[dict[str, Any]],
        language_pair: str,
    ) -> AICheckResult:
        """Check text assignment answers using GPT-4o."""
        source_lang, target_lang = self._parse_language_pair(language_pair)

        prompt = CHECK_PROMPT_TEXT.format(
            target_language=target_lang,
            source_language=source_lang,
            questions=json.dumps(questions, ensure_ascii=False, indent=2),
            answers=json.dumps(answers, ensure_ascii=False, indent=2),
        )

        try:
            response = await self._client.post(
                self.CHAT_URL,
                json={
                    "model": settings.openai.gpt_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            data = json.loads(content)

            return AICheckResult(
                score=max(0, min(100, int(data.get("score", 50)))),
                feedback=data.get("feedback", ""),
                detailed_results=data.get("detailed_results", []),
            )

        except httpx.HTTPError as e:
            logger.error(f"GPT-4o API error during checking: {e}")
            raise
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse GPT-4o response: {e}")
            return AICheckResult(
                score=0,
                feedback="He ydalos' proverit' otvety. Poprobyjte pozzhe.",
                detailed_results=[],
            )

    def check_multiple_choice(
        self,
        questions: list[dict[str, Any]],
        answers: list[dict[str, Any]],
    ) -> AICheckResult:
        """Check multiple choice answers (deterministic, no AI needed)."""
        correct_count = 0
        total = len(questions)
        detailed_results = []

        # Create answer lookup
        answer_map = {a["question_id"]: a.get("selected_index") for a in answers}

        for question in questions:
            q_id = question["id"]
            correct_idx = question.get("correct_index", 0)
            selected_idx = answer_map.get(q_id)

            is_correct = selected_idx == correct_idx
            if is_correct:
                correct_count += 1

            correct_answer = question["options"][correct_idx]
            detailed_results.append(
                {
                    "question_id": q_id,
                    "correct": is_correct,
                    "feedback": self._get_mc_feedback(
                        is_correct=is_correct,
                        correct_answer=correct_answer,
                    ),
                }
            )

        score = int((correct_count / total) * 100) if total > 0 else 0
        feedback = self._get_score_feedback(score)

        return AICheckResult(
            score=score,
            feedback=feedback,
            detailed_results=detailed_results,
        )

    async def check_voice_assignment(
        self,
        words: list[dict[str, Any]],  # noqa: ARG002
        recordings: list[dict[str, Any]],
    ) -> AICheckResult:
        """Aggregate voice pronunciation results."""
        # Voice checking is done by the voice module (Whisper + GPT)
        # This just aggregates the ratings from individual checks
        total_rating = 0
        count = 0
        detailed_results = []

        for recording in recordings:
            word_id = recording.get("word_id")
            rating = recording.get("rating", 0)
            total_rating += rating
            count += 1

            detailed_results.append(
                {
                    "question_id": word_id,
                    "correct": rating >= VOICE_CORRECT_THRESHOLD,
                    "feedback": f"Ocenka proiznosheniya: {rating}/5",
                }
            )

        avg_rating = total_rating / count if count > 0 else 0
        score = int((avg_rating / 5) * 100)
        feedback = self._get_voice_feedback(avg_rating)

        return AICheckResult(
            score=score,
            feedback=feedback,
            detailed_results=detailed_results,
        )

    def _get_mc_feedback(self, *, is_correct: bool, correct_answer: str) -> str:
        """Get feedback for multiple choice answer."""
        if is_correct:
            return "Pravil'no!"
        return f"Pravil'nyj otvet: {correct_answer}"

    def _get_score_feedback(self, score: int) -> str:
        """Get feedback based on score."""
        if score >= SCORE_EXCELLENT:
            return "Otlichno! Pochti vse otvety pravil'nye."
        if score >= SCORE_GOOD:
            return "Horosho! Bol'shinstvo otvetov vernye."
        if score >= SCORE_FAIR:
            return "Neploho, no est' nad chem porabotat'."
        return "Nuzhno povtorit' material. Poprobuj esche raz!"

    def _get_voice_feedback(self, avg_rating: float) -> str:
        """Get feedback based on voice rating."""
        if avg_rating >= VOICE_EXCELLENT:
            return "Prevoshodnoe proiznoshenie!"
        if avg_rating >= VOICE_GOOD:
            return "Ochen' horoshee proiznoshenie!"
        if avg_rating >= VOICE_FAIR:
            return "Horosho, no est' chto uluchshit'."
        return "Nuzhno bol'she praktiki. Slushaj nositelej yazyka!"

    def _parse_language_pair(self, language_pair: str) -> tuple[str, str]:
        """Parse language pair to human-readable names."""
        lang_names = {
            "en": "English",
            "ru": "Russian",
            "ko": "Korean",
        }
        parts = language_pair.split("_")
        source = lang_names.get(parts[0], parts[0]) if len(parts) > 0 else "English"
        target = lang_names.get(parts[1], parts[1]) if len(parts) > 1 else "Russian"
        return source, target

    def _extract_content(
        self,
        data: dict[str, Any],
        assignment_type: AssignmentType,
    ) -> dict[str, Any]:
        """Extract content based on assignment type."""
        if assignment_type == AssignmentType.VOICE:
            return {"words": data.get("words", [])}
        return {"questions": data.get("questions", [])}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


class _TeachingAIClientHolder:
    """Holder for singleton TeachingAIClient instance."""

    _instance: TeachingAIClient | None = None

    @classmethod
    def get(cls) -> TeachingAIClient:
        if cls._instance is None:
            cls._instance = TeachingAIClient()
        return cls._instance


def get_teaching_ai_client() -> TeachingAIClient:
    """Get the singleton TeachingAIClient instance."""
    return _TeachingAIClientHolder.get()
