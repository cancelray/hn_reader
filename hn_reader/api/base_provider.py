from abc import ABC, abstractmethod
from collections.abc import Sequence

from hn_reader.models import Comment, Feed, Story


class BaseProvider(ABC):
    @abstractmethod
    def open_client(self) -> None: ...

    @abstractmethod
    async def close_client(self) -> None: ...

    @abstractmethod
    async def fetch_feed_ids(self, feed: Feed) -> list[int]: ...

    @abstractmethod
    async def fetch_story(self, story_id: int) -> Story | None: ...

    @abstractmethod
    async def fetch_comments(self, ids: Sequence[int]) -> list[Comment]: ...
