"""Unit tests for SM-2 algorithm."""

import pytest

from src.modules.srs.algorithm import SM2Result, calculate_sm2


class TestSM2Algorithm:
    """Test cases for SM-2 spaced repetition algorithm."""

    # Test quality rating edge cases

    def test_quality_1_resets_repetitions(self) -> None:
        """Quality 1 (forgot) should reset repetitions to 0."""
        result = calculate_sm2(quality=1, repetitions=5, easiness=2.5, interval=30)

        assert result.repetitions == 0
        assert result.interval == 1
        assert result.easiness == 2.5  # noqa: PLR2004 - Easiness preserved on failure

    def test_quality_2_resets_repetitions(self) -> None:
        """Quality 2 (hard) should reset repetitions to 0."""
        result = calculate_sm2(quality=2, repetitions=3, easiness=2.5, interval=15)

        assert result.repetitions == 0
        assert result.interval == 1
        assert result.easiness == 2.5  # noqa: PLR2004

    def test_quality_3_is_passing(self) -> None:
        """Quality 3 should be passing (not reset)."""
        result = calculate_sm2(quality=3, repetitions=0, easiness=2.5, interval=0)

        assert result.repetitions == 1
        assert result.interval == 1  # First repetition

    def test_quality_4_is_passing(self) -> None:
        """Quality 4 should be passing."""
        result = calculate_sm2(quality=4, repetitions=1, easiness=2.5, interval=1)

        assert result.repetitions == 2  # noqa: PLR2004
        assert result.interval == 6  # noqa: PLR2004 - Second repetition

    def test_quality_5_is_passing(self) -> None:
        """Quality 5 (perfect) should be passing with best easiness."""
        result = calculate_sm2(quality=5, repetitions=2, easiness=2.5, interval=6)

        assert result.repetitions == 3  # noqa: PLR2004
        assert result.interval == 16  # noqa: PLR2004 - round(6 * 2.6) since easiness increases
        assert result.easiness > 2.5  # noqa: PLR2004 - Easiness increases

    # Test interval progression

    def test_first_correct_answer_sets_interval_to_1(self) -> None:
        """First correct answer should set interval to 1 day."""
        result = calculate_sm2(quality=4, repetitions=0, easiness=2.5, interval=0)

        assert result.interval == 1
        assert result.repetitions == 1

    def test_second_correct_answer_sets_interval_to_6(self) -> None:
        """Second correct answer should set interval to 6 days."""
        result = calculate_sm2(quality=4, repetitions=1, easiness=2.5, interval=1)

        assert result.interval == 6  # noqa: PLR2004
        assert result.repetitions == 2  # noqa: PLR2004

    def test_subsequent_intervals_multiply_by_easiness(self) -> None:
        """Subsequent intervals should multiply by easiness factor."""
        result = calculate_sm2(quality=4, repetitions=2, easiness=2.5, interval=6)

        assert result.interval == 15  # noqa: PLR2004 - round(6 * 2.5)
        assert result.repetitions == 3  # noqa: PLR2004

    def test_long_interval_progression(self) -> None:
        """Test interval progression over multiple repetitions."""
        # Start fresh
        r = calculate_sm2(quality=4, repetitions=0, easiness=2.5, interval=0)
        assert r.interval == 1

        # Second rep
        r = calculate_sm2(quality=4, repetitions=1, easiness=r.easiness, interval=1)
        assert r.interval == 6  # noqa: PLR2004

        # Third rep
        r = calculate_sm2(quality=4, repetitions=2, easiness=r.easiness, interval=6)
        assert r.interval == round(6 * r.easiness)

    # Test easiness factor

    def test_perfect_answer_increases_easiness(self) -> None:
        """Quality 5 should increase easiness factor."""
        result = calculate_sm2(quality=5, repetitions=2, easiness=2.5, interval=6)

        assert result.easiness > 2.5  # noqa: PLR2004

    def test_quality_3_decreases_easiness(self) -> None:
        """Quality 3 should decrease easiness factor."""
        result = calculate_sm2(quality=3, repetitions=2, easiness=2.5, interval=6)

        assert result.easiness < 2.5  # noqa: PLR2004

    def test_easiness_never_drops_below_1_3(self) -> None:
        """Easiness factor should never drop below 1.3."""
        # Use minimum easiness and lowest passing quality
        result = calculate_sm2(quality=3, repetitions=2, easiness=1.3, interval=6)

        assert result.easiness >= 1.3  # noqa: PLR2004

    def test_easiness_preserved_on_failure(self) -> None:
        """Easiness should be preserved when answer is wrong."""
        original_easiness = 2.2
        result = calculate_sm2(quality=1, repetitions=5, easiness=original_easiness, interval=30)

        assert result.easiness == original_easiness

    # Test SM2Result

    def test_sm2_result_is_dataclass(self) -> None:
        """SM2Result should be a proper dataclass."""
        result = SM2Result(repetitions=1, easiness=2.5, interval=6)

        assert result.repetitions == 1
        assert result.easiness == 2.5  # noqa: PLR2004
        assert result.interval == 6  # noqa: PLR2004

    def test_sm2_result_is_frozen(self) -> None:
        """SM2Result should be immutable (frozen)."""
        result = SM2Result(repetitions=1, easiness=2.5, interval=6)

        with pytest.raises(AttributeError):
            result.repetitions = 2  # type: ignore[misc]

    # Test specific calculations

    def test_easiness_calculation_quality_5(self) -> None:
        """Test easiness calculation for quality 5."""
        # EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        # For q=5: EF' = 2.5 + (0.1 - 0 * (0.08 + 0)) = 2.5 + 0.1 = 2.6
        result = calculate_sm2(quality=5, repetitions=2, easiness=2.5, interval=6)

        assert result.easiness == 2.6  # noqa: PLR2004

    def test_easiness_calculation_quality_4(self) -> None:
        """Test easiness calculation for quality 4."""
        # For q=4: EF' = 2.5 + (0.1 - 1 * (0.08 + 1*0.02)) = 2.5 + 0.1 - 0.1 = 2.5
        result = calculate_sm2(quality=4, repetitions=2, easiness=2.5, interval=6)

        assert result.easiness == 2.5  # noqa: PLR2004

    def test_easiness_calculation_quality_3(self) -> None:
        """Test easiness calculation for quality 3."""
        # For q=3: EF' = 2.5 + (0.1 - 2 * (0.08 + 2*0.02)) = 2.5 + 0.1 - 0.24 = 2.36
        result = calculate_sm2(quality=3, repetitions=2, easiness=2.5, interval=6)

        assert result.easiness == 2.36  # noqa: PLR2004

    # Test real-world scenarios

    def test_word_learning_scenario(self) -> None:
        """Test a realistic word learning scenario."""
        # Day 1: First encounter, correct
        r = calculate_sm2(quality=4, repetitions=0, easiness=2.5, interval=0)
        assert r == SM2Result(repetitions=1, easiness=2.5, interval=1)

        # Day 2: Second encounter, correct
        r = calculate_sm2(quality=4, repetitions=1, easiness=2.5, interval=1)
        assert r == SM2Result(repetitions=2, easiness=2.5, interval=6)

        # Day 8: Third encounter, correct
        r = calculate_sm2(quality=4, repetitions=2, easiness=2.5, interval=6)
        assert r == SM2Result(repetitions=3, easiness=2.5, interval=15)

        # Day 23: Fourth encounter, forgot
        r = calculate_sm2(quality=1, repetitions=3, easiness=2.5, interval=15)
        assert r == SM2Result(repetitions=0, easiness=2.5, interval=1)

        # Day 24: Back to first repetition
        r = calculate_sm2(quality=4, repetitions=0, easiness=2.5, interval=0)
        assert r == SM2Result(repetitions=1, easiness=2.5, interval=1)
