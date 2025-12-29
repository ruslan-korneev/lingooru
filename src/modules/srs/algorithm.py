"""SM-2 spaced repetition algorithm implementation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SM2Result:
    """Result of SM-2 calculation."""

    repetitions: int
    easiness: float
    interval: int  # days


def calculate_sm2(
    quality: int,
    repetitions: int,
    easiness: float,
    interval: int,
) -> SM2Result:
    """
    Calculate next SM-2 parameters based on quality rating.

    Args:
        quality: Rating 1-5 (1=forgot, 5=perfect recall)
        repetitions: Current number of successful repetitions
        easiness: Current easiness factor (EF), minimum 1.3
        interval: Current interval in days

    Returns:
        SM2Result with new repetitions, easiness, and interval

    Note:
        Quality 1-2 is considered a failure (resets progress).
        Quality 3-5 is considered a pass.
    """
    # Map 1-5 scale to internal SM-2 quality (where < 3 is fail)
    # 1,2 -> fail, 3,4,5 -> pass
    if quality <= 2:  # noqa: PLR2004
        # Failed recall - reset repetitions, start over
        return SM2Result(
            repetitions=0,
            easiness=easiness,
            interval=1,
        )

    # Update easiness factor using SM-2 formula
    # EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
    new_easiness = max(
        1.3,
        easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02),
    )

    # Calculate new interval
    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = round(interval * new_easiness)

    return SM2Result(
        repetitions=repetitions + 1,
        easiness=round(new_easiness, 2),
        interval=new_interval,
    )
