from uuid import uuid4

from fastapi import status
from httpx import AsyncClient

from src.modules.users.dto import UserReadDTO

TELEGRAM_ID_CREATE = 555666777
TELEGRAM_ID_SAMPLE = 123456789


class TestUsersAPI:
    async def test_create_user(self, api_client: AsyncClient) -> None:
        response = await api_client.post(
            "/v1/users",
            json={
                "telegram_id": TELEGRAM_ID_CREATE,
                "username": "apiuser",
                "first_name": "API User",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["telegram_id"] == TELEGRAM_ID_CREATE
        assert data["username"] == "apiuser"
        assert data["ui_language"] == "ru"
        assert data["language_pair"] == "en_ru"

    async def test_get_user_by_id(
        self,
        api_client: AsyncClient,
        sample_user: UserReadDTO,
    ) -> None:
        response = await api_client.get(f"/v1/users/{sample_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["telegram_id"] == sample_user.telegram_id

    async def test_get_user_by_telegram_id(
        self,
        api_client: AsyncClient,
        sample_user: UserReadDTO,
    ) -> None:
        response = await api_client.get(
            f"/v1/users/telegram/{sample_user.telegram_id}",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_user.id)

    async def test_update_user(
        self,
        api_client: AsyncClient,
        sample_user: UserReadDTO,
    ) -> None:
        response = await api_client.patch(
            f"/v1/users/{sample_user.id}",
            json={"ui_language": "en"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ui_language"] == "en"

    async def test_list_users_paginated(
        self,
        api_client: AsyncClient,
        sample_user: UserReadDTO,  # noqa: ARG002
        second_sample_user: UserReadDTO,  # noqa: ARG002
    ) -> None:
        response = await api_client.get(
            "/v1/users",
            params={"limit": 10, "offset": 0},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "has_more" in data

    async def test_get_user_not_found(self, api_client: AsyncClient) -> None:
        response = await api_client.get(f"/v1/users/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_user_conflict(
        self,
        api_client: AsyncClient,
        sample_user: UserReadDTO,
    ) -> None:
        response = await api_client.post(
            "/v1/users",
            json={"telegram_id": sample_user.telegram_id},
        )

        assert response.status_code == status.HTTP_409_CONFLICT
