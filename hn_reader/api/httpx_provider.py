import asyncio
from collections.abc import Sequence

import httpx

from hn_reader import Config
from hn_reader.exceptions import HnNetworkError, HnServerError, HnTimeoutError
from hn_reader.models import Comment, Feed, Story

from .base_provider import BaseProvider


class HttpxProvider(BaseProvider):
    def __init__(self, config: Config) -> None:
        self.config = config
        self.client: httpx.AsyncClient | None = None
        self._timeout_retries = self.config.timeout_retries.copy()
        self._max_attempts = len(self._timeout_retries) + 1

    def open_client(self) -> None:
        timeout = httpx.Timeout(
            timeout=self.config.timeout, connect=self.config.connect
        )

        limits = httpx.Limits(max_connections=self.config.max_connection)

        headers = {
            'User-Agent': self.config.user_agent,
            'Accept': 'application/json',
        }

        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=timeout,
            limits=limits,
            headers=headers,
        )

    async def close_client(self) -> None:
        if self.client:
            await self.client.aclose()

    async def fetch_feed_ids(self, feed: Feed) -> list[int]:
        if self.client:
            for attempt in range(self._max_attempts):
                try:
                    response = await self.client.get(f'{feed.endpoint}.json')

                    if response.status_code >= 500 and attempt < len(
                        self._timeout_retries
                    ):
                        await asyncio.sleep(self._timeout_retries[attempt])
                        continue

                    response.raise_for_status()
                    data = response.json()
                    feed_ids = [int(item) for item in data]

                    return feed_ids
                except httpx.TimeoutException as e:
                    raise HnTimeoutError(
                        'Время ожидания истекло. Не удалось загрузить данные. Проверьте подключение к интернету и нажмите r для повторной загрузки.',
                        None,
                    ) from e
                except httpx.NetworkError as e:
                    raise HnNetworkError(
                        'Ошибка сети. Не удалось связаться с сервером. Проверьте подключение к интернету и нажмите r для повторной загрузки',
                        None,
                    ) from e
                except httpx.HTTPStatusError as e:
                    raise HnServerError(
                        'Не удалось загрузить данные. Нажмите r для повторной загрузки или повторить попытку позже',
                        e.response.status_code,
                    ) from e

        return []

    async def fetch_story(self, story_id: int) -> Story | None:
        if self.client:
            async with asyncio.Semaphore(10):
                for attempt in range(self._max_attempts):
                    try:
                        response = await self.client.get(f'/item/{story_id}.json')

                        if response.status_code >= 500 and attempt < len(
                            self._timeout_retries
                        ):
                            await asyncio.sleep(self._timeout_retries[attempt])
                            continue

                        response.raise_for_status()
                        data = response.json()

                        if data:
                            return Story.from_api(data)
                    except httpx.TimeoutException as e:
                        raise HnTimeoutError(
                            'Время ожидания истекло. Не удалось загрузить данные. Проверьте подключение к интернету и нажмите r для повторной загрузки.',
                            None,
                        ) from e
                    except httpx.NetworkError as e:
                        raise HnNetworkError(
                            'Ошибка сети. Не удалось связаться с сервером. Проверьте подключение к интернету и нажмите r для повторной загрузки',
                            None,
                        ) from e
                    except httpx.HTTPStatusError as e:
                        raise HnServerError(
                            'Не удалось загрузить данные. Нажмите r для повторной загрузки или повторить попытку позже',
                            e.response.status_code,
                        ) from e

    async def _fetch_comment(
        self, id: int, client: httpx.AsyncClient
    ) -> Comment | None:
        for attempt in range(self._max_attempts):
            response = await client.get(f'/item/{id}.json')

            if response.status_code >= 500 and attempt < len(self._timeout_retries):
                await asyncio.sleep(self._timeout_retries[attempt])
                continue

            response.raise_for_status()
            data = response.json()

            if data:
                return Comment.from_api(data)

        return None

    async def fetch_comments(self, ids: Sequence[int]) -> list[Comment]:
        if self.client:
            try:
                tasks = [self._fetch_comment(id, self.client) for id in ids]

                comments = await asyncio.gather(*tasks)

                return [comment for comment in comments if comment is not None]
            except httpx.TimeoutException as e:
                raise HnTimeoutError(
                    'Время ожидания истекло. Не удалось загрузить данные. Проверьте подключение к интернету и нажмите r для повторной загрузки.',
                    None,
                ) from e
            except httpx.NetworkError as e:
                raise HnNetworkError(
                    'Ошибка сети. Не удалось связаться с сервером. Проверьте подключение к интернету и нажмите r для повторной загрузки',
                    None,
                ) from e
            except httpx.HTTPStatusError as e:
                raise HnServerError(
                    'Не удалось загрузить данные. Нажмите r для повторной загрузки или повторить попытку позже',
                    e.response.status_code,
                ) from e

        return []
