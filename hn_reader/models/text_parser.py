from html import unescape
from html.parser import HTMLParser


class TextParser(HTMLParser):
    def __init__(self, *args, **kwargs) -> None:
        self._text_parts: list[str] = []
        self._in_link = False
        super().__init__(*args, **kwargs)

    def reset(self) -> None:
        super().reset()
        self._text_parts = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == 'p':
            self._text_parts.append('\n\n')
        elif tag == 'br':
            self._text_parts.append('\n')
        elif tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self._text_parts.append(href)
                self._in_link = True

    def handle_endtag(self, tag: str) -> None:
        if tag == 'a':
            self._in_link = False

    def handle_data(self, data: str) -> None:
        if not self._in_link:
            self._text_parts.append(data)

    def get_text(self) -> str:
        text = unescape('\n'.join(self._text_parts))
        lines = [line.strip() for line in text.splitlines()]
        return ''.join(lines).strip()
