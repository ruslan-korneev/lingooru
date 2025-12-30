"""Tests for TeachingAIClient."""

import json

import pytest
from pytest_httpx import HTTPXMock

from src.modules.teaching.ai_client import (
    SCORE_EXCELLENT,
    SCORE_FAIR,
    SCORE_GOOD,
    VOICE_EXCELLENT,
    VOICE_FAIR,
    VOICE_GOOD,
    AICheckResult,
    GeneratedAssignment,
    TeachingAIClient,
)
from src.modules.teaching.enums import AssignmentType

# Expected test values
EXPECTED_SCORE_85 = 85
EXPECTED_SCORE_100 = 100
EXPECTED_SCORE_60 = 60
EXPECTED_SCORE_50 = 50
EXPECTED_RESULTS_COUNT_2 = 2
EXPECTED_FEEDBACK_SCORE_30 = 30
EXPECTED_VOICE_RATING_2 = 2


@pytest.fixture
def ai_client() -> TeachingAIClient:
    return TeachingAIClient()


class TestGenerateAssignment:
    async def test_generate_text_assignment(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "title": "Vocabulary Test",
                                "description": "Translate words",
                                "questions": [{"id": "q1", "text": "apple", "expected": "яблоко"}],
                            }
                        )
                    }
                }
            ]
        }
        httpx_mock.add_response(json=mock_response)

        result = await ai_client.generate_assignment(
            topic="fruits",
            assignment_type=AssignmentType.TEXT,
            language_pair="en_ru",
            difficulty="easy",
            question_count=1,
        )

        assert isinstance(result, GeneratedAssignment)
        assert result.title == "Vocabulary Test"
        assert result.description == "Translate words"
        assert "questions" in result.content

    async def test_generate_voice_assignment(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "title": "Pronunciation",
                                "description": "Practice words",
                                "words": [{"id": "w1", "text": "hello", "phonetic": None}],
                            }
                        )
                    }
                }
            ]
        }
        httpx_mock.add_response(json=mock_response)

        result = await ai_client.generate_assignment(
            topic="greetings",
            assignment_type=AssignmentType.VOICE,
            language_pair="en_ru",
        )

        assert "words" in result.content
        assert len(result.content["words"]) == 1

    async def test_generate_mc_assignment(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "title": "Quiz",
                                "description": "Choose correct",
                                "questions": [
                                    {
                                        "id": "q1",
                                        "text": "What is apple?",
                                        "options": ["яблоко", "банан", "груша"],
                                        "correct_index": 0,
                                    }
                                ],
                            }
                        )
                    }
                }
            ]
        }
        httpx_mock.add_response(json=mock_response)

        result = await ai_client.generate_assignment(
            topic="fruits",
            assignment_type=AssignmentType.MULTIPLE_CHOICE,
            language_pair="ko_ru",
        )

        assert "questions" in result.content
        assert "correct_index" in result.content["questions"][0]

    async def test_generate_with_default_title(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "description": "Test",
                                "questions": [],
                            }
                        )
                    }
                }
            ]
        }
        httpx_mock.add_response(json=mock_response)

        result = await ai_client.generate_assignment(
            topic="my topic",
            assignment_type=AssignmentType.TEXT,
            language_pair="en_ru",
        )

        assert result.title == "Assignment: my topic"

    async def test_generate_http_error(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        import httpx

        httpx_mock.add_response(status_code=500)

        with pytest.raises(httpx.HTTPStatusError):
            await ai_client.generate_assignment(
                topic="test",
                assignment_type=AssignmentType.TEXT,
                language_pair="en_ru",
            )

    async def test_generate_json_decode_error(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {"choices": [{"message": {"content": "not valid json"}}]}
        httpx_mock.add_response(json=mock_response)

        with pytest.raises(json.JSONDecodeError):
            await ai_client.generate_assignment(
                topic="test",
                assignment_type=AssignmentType.TEXT,
                language_pair="en_ru",
            )


class TestCheckTextAssignment:
    async def test_check_text_assignment_success(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "score": 85,
                                "feedback": "Great job!",
                                "detailed_results": [{"question_id": "q1", "correct": True, "feedback": "Correct"}],
                            }
                        )
                    }
                }
            ]
        }
        httpx_mock.add_response(json=mock_response)

        result = await ai_client.check_text_assignment(
            questions=[{"id": "q1", "text": "apple", "expected": "яблоко"}],
            answers=[{"question_id": "q1", "answer": "яблоко"}],
            language_pair="en_ru",
        )

        assert isinstance(result, AICheckResult)
        assert result.score == EXPECTED_SCORE_85
        assert result.feedback == "Great job!"
        assert len(result.detailed_results) == 1

    async def test_check_text_clamps_score(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {"choices": [{"message": {"content": json.dumps({"score": 150, "feedback": "Test"})}}]}
        httpx_mock.add_response(json=mock_response)

        result = await ai_client.check_text_assignment([], [], "en_ru")

        assert result.score == EXPECTED_SCORE_100  # Clamped to max

    async def test_check_text_clamps_negative_score(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {"choices": [{"message": {"content": json.dumps({"score": -10, "feedback": "Test"})}}]}
        httpx_mock.add_response(json=mock_response)

        result = await ai_client.check_text_assignment([], [], "en_ru")

        assert result.score == 0  # Clamped to min

    async def test_check_text_json_error_returns_fallback(
        self,
        ai_client: TeachingAIClient,
        httpx_mock: HTTPXMock,
    ) -> None:
        mock_response = {"choices": [{"message": {"content": "invalid json"}}]}
        httpx_mock.add_response(json=mock_response)

        result = await ai_client.check_text_assignment([], [], "en_ru")

        assert result.score == 0
        assert result.feedback != ""


class TestCheckMultipleChoice:
    def test_all_correct(self, ai_client: TeachingAIClient) -> None:
        questions = [
            {"id": "q1", "text": "Test", "options": ["A", "B", "C"], "correct_index": 0},
            {"id": "q2", "text": "Test2", "options": ["X", "Y", "Z"], "correct_index": 2},
        ]
        answers = [
            {"question_id": "q1", "selected_index": 0},
            {"question_id": "q2", "selected_index": 2},
        ]

        result = ai_client.check_multiple_choice(questions, answers)

        assert result.score == EXPECTED_SCORE_100
        assert len(result.detailed_results) == EXPECTED_RESULTS_COUNT_2
        assert all(r["correct"] for r in result.detailed_results)

    def test_all_wrong(self, ai_client: TeachingAIClient) -> None:
        questions = [
            {"id": "q1", "text": "Test", "options": ["A", "B", "C"], "correct_index": 0},
        ]
        answers = [
            {"question_id": "q1", "selected_index": 1},
        ]

        result = ai_client.check_multiple_choice(questions, answers)

        assert result.score == 0
        assert not result.detailed_results[0]["correct"]
        assert "A" in result.detailed_results[0]["feedback"]  # Contains correct answer

    def test_partial_correct(self, ai_client: TeachingAIClient) -> None:
        questions = [
            {"id": "q1", "text": "Q1", "options": ["A", "B"], "correct_index": 0},
            {"id": "q2", "text": "Q2", "options": ["X", "Y"], "correct_index": 0},
        ]
        answers = [
            {"question_id": "q1", "selected_index": 0},
            {"question_id": "q2", "selected_index": 1},
        ]

        result = ai_client.check_multiple_choice(questions, answers)

        assert result.score == EXPECTED_SCORE_50

    def test_empty_questions(self, ai_client: TeachingAIClient) -> None:
        result = ai_client.check_multiple_choice([], [])
        assert result.score == 0


class TestCheckVoiceAssignment:
    async def test_excellent_voice(self, ai_client: TeachingAIClient) -> None:
        words = [{"id": "w1", "text": "hello"}]
        recordings = [{"word_id": "w1", "rating": 5}]

        result = await ai_client.check_voice_assignment(words, recordings)

        assert result.score == EXPECTED_SCORE_100
        assert result.detailed_results[0]["correct"] is True

    async def test_average_voice(self, ai_client: TeachingAIClient) -> None:
        words = [{"id": "w1", "text": "hello"}]
        recordings = [{"word_id": "w1", "rating": 3}]

        result = await ai_client.check_voice_assignment(words, recordings)

        assert result.score == EXPECTED_SCORE_60
        assert result.detailed_results[0]["correct"] is False

    async def test_empty_recordings(self, ai_client: TeachingAIClient) -> None:
        result = await ai_client.check_voice_assignment([], [])
        assert result.score == 0


class TestScoreFeedback:
    def test_excellent_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_score_feedback(SCORE_EXCELLENT)  # noqa: SLF001
        assert "Otlichno" in feedback

    def test_good_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_score_feedback(SCORE_GOOD)  # noqa: SLF001
        assert "Horosho" in feedback

    def test_fair_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_score_feedback(SCORE_FAIR)  # noqa: SLF001
        assert "Neploho" in feedback

    def test_low_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_score_feedback(EXPECTED_FEEDBACK_SCORE_30)  # noqa: SLF001
        assert "povtorit" in feedback.lower()


class TestVoiceFeedback:
    def test_excellent_voice_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_voice_feedback(VOICE_EXCELLENT)  # noqa: SLF001
        assert "Prevoshodnoe" in feedback

    def test_good_voice_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_voice_feedback(VOICE_GOOD)  # noqa: SLF001
        assert "Ochen' horoshee" in feedback

    def test_fair_voice_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_voice_feedback(VOICE_FAIR)  # noqa: SLF001
        assert "uluchshit" in feedback

    def test_low_voice_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_voice_feedback(EXPECTED_VOICE_RATING_2)  # noqa: SLF001
        assert "praktiki" in feedback.lower()


class TestParseLanguagePair:
    def test_en_ru(self, ai_client: TeachingAIClient) -> None:
        source, target = ai_client._parse_language_pair("en_ru")  # noqa: SLF001
        assert source == "English"
        assert target == "Russian"

    def test_ko_ru(self, ai_client: TeachingAIClient) -> None:
        source, target = ai_client._parse_language_pair("ko_ru")  # noqa: SLF001
        assert source == "Korean"
        assert target == "Russian"

    def test_unknown_language(self, ai_client: TeachingAIClient) -> None:
        source, target = ai_client._parse_language_pair("es_fr")  # noqa: SLF001
        assert source == "es"
        assert target == "fr"

    def test_empty_string(self, ai_client: TeachingAIClient) -> None:
        source, target = ai_client._parse_language_pair("")  # noqa: SLF001
        # Should handle gracefully
        assert isinstance(source, str)
        assert isinstance(target, str)


class TestClientLifecycle:
    async def test_close(self, ai_client: TeachingAIClient) -> None:
        await ai_client.close()
        # Client should be closed - subsequent calls would fail


class TestMCFeedback:
    def test_correct_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_mc_feedback(is_correct=True, correct_answer="A")  # noqa: SLF001
        assert "Pravil'no" in feedback

    def test_wrong_feedback(self, ai_client: TeachingAIClient) -> None:
        feedback = ai_client._get_mc_feedback(is_correct=False, correct_answer="B")  # noqa: SLF001
        assert "B" in feedback


class TestExtractContent:
    def test_extract_voice_content(self, ai_client: TeachingAIClient) -> None:
        data = {"words": [{"id": "w1"}], "questions": [{"id": "q1"}]}
        content = ai_client._extract_content(data, AssignmentType.VOICE)  # noqa: SLF001
        assert "words" in content
        assert "questions" not in content

    def test_extract_text_content(self, ai_client: TeachingAIClient) -> None:
        data = {"words": [{"id": "w1"}], "questions": [{"id": "q1"}]}
        content = ai_client._extract_content(data, AssignmentType.TEXT)  # noqa: SLF001
        assert "questions" in content
        assert "words" not in content

    def test_extract_mc_content(self, ai_client: TeachingAIClient) -> None:
        data = {"questions": [{"id": "q1"}]}
        content = ai_client._extract_content(data, AssignmentType.MULTIPLE_CHOICE)  # noqa: SLF001
        assert "questions" in content
