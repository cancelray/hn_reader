from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from hn_reader.models.text_parser import TextParser


@dataclass(frozen=True, slots=True)
class Story:
    id: int
    title: str
    url: str | None
    _text: str | None
    author: str
    score: int
    comments_count: int
    created_at: datetime
    kids: tuple[int, ...]
    _parser: TextParser

    @property
    def age(self) -> str:
        now = datetime.now(timezone.utc)
        delta = now - self.created_at

        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f'{seconds}s'

        minutes = seconds // 60
        if minutes < 60:
            return f'{minutes}m'

        hours = minutes // 60
        if hours < 24:
            return f'{hours}h'

        days = hours // 24
        if days < 365:
            return f'{days}d'

        years = days // 365
        return f'{years}y'

    @property
    def text(self) -> str | None:
        if self._text:
            self._parser.feed(self._text)
            parse_result = self._parser.get_text()
            self._parser.close()
            self._parser.reset()
            return parse_result

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> 'Story':
        return cls(
            id=data['id'],
            title=data.get('title', ''),
            url=data.get('url'),
            _text=data.get('text', ''),
            author=data.get('by', 'unknown'),
            score=data.get('score', 0),
            comments_count=data.get('descendants', 0),
            created_at=datetime.fromtimestamp(data['time'], tz=timezone.utc),
            kids=tuple(data.get('kids', ())),
            _parser=TextParser()
        )
