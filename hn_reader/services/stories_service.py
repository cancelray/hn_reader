import time
from collections.abc import AsyncGenerator

from hn_reader.api import BaseProvider
from hn_reader.models import Comment, Feed, Story

from .base_stories_service import BaseStoriesService


class StoriesService(BaseStoriesService):
    def __init__(self, client: BaseProvider) -> None:
        self.client = client
        self._cache: dict[str, tuple[list[Story], float]] = {}

    async def load_feed(
        self,
        feed: Feed,
        limit: int = 30,
        force: bool = False,
    ) -> AsyncGenerator[Story, None]:
        cache_key = feed.endpoint
        story_resp_list: list[Story] = []

        if cache_key in self._cache and force == False:
            data, cache_time_limit = self._cache[cache_key]

            if time.monotonic() < cache_time_limit:
                for story in data:
                    yield story

            return

        feed_ids = await self.client.fetch_feed_ids(feed)
        target_ids = feed_ids[:limit]

        for id in target_ids:
            story_resp = await self.client.fetch_story(id)

            if story_resp:
                cache_time_limit = time.monotonic() + 60
                story_resp_list.append(story_resp)
                self._cache[cache_key] = story_resp_list, cache_time_limit

                yield story_resp

    async def load_comments(self, story: Story, limit: int) -> list[Comment]:
        comments_ids = story.kids
        target_comments_ids = comments_ids[:limit]

        comments = await self.client.fetch_comments(target_comments_ids)

        return [comment for comment in comments if comment is not None]
