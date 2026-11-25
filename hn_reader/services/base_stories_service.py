from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from hn_reader.models import Comment, Feed, Story


class BaseStoriesService(ABC):
    @abstractmethod
    def load_feed(
        self,
        feed: Feed,
        limit: int = 30,
        force: bool = False,
        on_progress: dict[str, int] | None = None,
    ) -> AsyncGenerator[Story, None]: ...

    @abstractmethod
    async def load_comments(self, story: Story, limit: int) -> list[Comment]: ...
