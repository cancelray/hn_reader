from dataclasses import dataclass

from hn_reader.models.text_parser import TextParser


@dataclass(frozen=True, slots=True)
class Comment:
    id: int
    author: str
    _text: str
    _parser: TextParser

    @property
    def text(self) -> str | None:
        if self._text:
            self._parser.feed(self._text)
            parse_result = self._parser.get_text()
            self._parser.close()
            self._parser.reset()
            return parse_result

    @classmethod
    def from_api(cls, data: dict) -> 'Comment':
        return cls(
            id=data['id'],
            author=data.get('by', '[deleted]'),
            _text=data.get('text', ''),
            _parser=TextParser(),
        )
