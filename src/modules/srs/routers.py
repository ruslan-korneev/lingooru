"""SRS API endpoints for review management."""

from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from src.core.dependencies.containers import Container
from src.core.exceptions import NotFoundError
from src.core.types.dto import PaginatedResponse
from src.db.session import AsyncSessionMaker
from src.modules.srs.dto import (
    DueReviewsCountDTO,
    ReviewRateRequestDTO,
    ReviewReadDTO,
    ReviewWithWordDTO,
)
from src.modules.srs.services import SRSService
from src.modules.vocabulary.enums import Language

router = APIRouter(prefix="/reviews", tags=["reviews"])

REVIEW_NOT_FOUND = "Review not found"


@router.get("/due/{user_id}")
@inject
async def get_due_reviews(
    user_id: UUID,
    db_session_maker: Annotated[
        AsyncSessionMaker,
        Depends(Provide[Container.db_session_maker]),
    ],
    target_language: Annotated[Language, Query()] = Language.RU,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> PaginatedResponse[ReviewWithWordDTO]:
    """Get words due for review for a user."""
    async with db_session_maker as session:
        service = SRSService(session)
        reviews = await service.get_due_reviews(
            user_id=user_id,
            target_language=target_language,
            limit=limit,
        )
        return PaginatedResponse.create(
            items=list(reviews),
            total=len(reviews),
            limit=limit,
            offset=0,
        )


@router.get("/count/{user_id}")
@inject
async def count_due_reviews(
    user_id: UUID,
    db_session_maker: Annotated[
        AsyncSessionMaker,
        Depends(Provide[Container.db_session_maker]),
    ],
) -> DueReviewsCountDTO:
    """Count reviews due for a user."""
    async with db_session_maker as session:
        service = SRSService(session)
        count = await service.count_due_reviews(user_id)
        return DueReviewsCountDTO(count=count)


@router.get("/{review_id}")
@inject
async def get_review(
    review_id: UUID,
    db_session_maker: Annotated[
        AsyncSessionMaker,
        Depends(Provide[Container.db_session_maker]),
    ],
) -> ReviewReadDTO:
    """Get review by ID."""
    async with db_session_maker as session:
        service = SRSService(session)
        review = await service.get_review_by_id(review_id)
        if not review:
            raise NotFoundError(REVIEW_NOT_FOUND)
        return review


@router.post("/{review_id}/rate")
@inject
async def rate_review(
    review_id: UUID,
    dto: ReviewRateRequestDTO,
    db_session_maker: Annotated[
        AsyncSessionMaker,
        Depends(Provide[Container.db_session_maker]),
    ],
) -> ReviewReadDTO:
    """Submit quality rating for a review and update SM-2 parameters."""
    async with db_session_maker as session:
        service = SRSService(session)

        # Verify review exists
        review = await service.get_review_by_id(review_id)
        if not review:
            raise NotFoundError(REVIEW_NOT_FOUND)

        # Record the review
        await service.record_review(
            review_id=review_id,
            quality=dto.quality,
            response_time_ms=dto.response_time_ms,
        )
        await session.commit()

        # Return updated review
        updated = await service.get_review_by_id(review_id)
        if not updated:
            raise NotFoundError(REVIEW_NOT_FOUND)
        return updated
