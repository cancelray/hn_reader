import re
import webbrowser
from pathlib import Path
from typing import Any

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Markdown,
    Tab,
    Tabs,
)

from hn_reader.config import Config
from hn_reader.exceptions import HnException
from hn_reader.models import Feed, Story
from hn_reader.services import BaseStoriesService
from hn_reader.ui.widgets import TableWidget


class MainScreen(Screen):
    def __init__(
        self, config: Config, stories_service: BaseStoriesService, *args, **kwargs
    ) -> None:
        self.config = config
        self.stories_service = stories_service
        self._stories: dict[int, Story] = {}
        self._saved_stories_path = (
            Path(__file__).resolve().parent.parent.parent.parent / 'saved-stories'
        )
        self._current_row: list[Any] = []
        super().__init__(*args, **kwargs)

    CSS_PATH = 'styles.tcss'

    BINDINGS = (
        ('r', 'reload', 'Обновить'),
        ('o', 'open', 'Открыть'),
        ('←→', '', 'Вкладка'),
        ('s', 'save', 'Сохранить (только текст)'),
        ('q', 'quit', 'Выход'),
    )

    def compose(self) -> ComposeResult:
        yield Header()
        yield Tabs(Tab('Top', id='top'), Tab('New', id='new'), Tab('Best', id='best'))
        with Horizontal(id='horizontal-content'):
            yield TableWidget(id='table-widget')
            with VerticalScroll():
                yield Markdown('Выберите историю для загрузки', id='details')
        yield Footer()

    @work(exclusive=True)
    async def on_tab_switch_load(self, feed: Feed, force: bool = False) -> None:
        table = self.query_one('#table', DataTable)
        table.clear()

        try:
            async for story in self.stories_service.load_feed(feed, force=force):
                self._stories[story.id] = story
                crop_title = Text(story.title, no_wrap=True, overflow='ellipsis')

                table.add_row(
                    story.id, crop_title, story.score, story.comments_count, story.age
                )
        except HnException as e:
            self.notify(e.message)

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        tab_id = event.tab.id
        current_tab = Feed(tab_id)
        self.on_tab_switch_load(current_tab)

    async def on_data_table_row_selected(
        self, event: DataTable.RowLabelSelected
    ) -> None:
        table = self.query_one('#table', DataTable)

        row = table.get_row(event.row_key)

        if row == self._current_row:
            return

        self._current_row = row

        details_widget = self.query_one('#details', Markdown)
        details_widget.loading = True

        story_id = int(row[0])
        story = self._stories[story_id]

        if story:
            title = f'{story.title}'
            author = f'Author: {story.author}'
            score = f'Score: {story.score}'
            comments_count = f'Comments: {story.comments_count}'
            posted = f'Posted: {story.created_at:%Y-%m-%d}'
            content = story.text
            if story.url:
                url = f'URL: {story.url}'
                content = url

            comments = await self.stories_service.load_comments(
                story, self.config.top_comments_load_limit
            )

            comments_title = '-----Top comments-----'
            comments_block = 'No comments yet'

            if comments:
                format_comments: list[str] = []

                for comment in comments:
                    format_comments.append(f'{comment.author}: {comment.text}')

                comments_block = '\\\n'.join(format_comments)

            details_widget.update(
                f'{title}\n\n{author}\\\n{score}\\\n{comments_count}\\\n{posted}\\\n{content}\n\n{comments_title}\n\n{comments_block}'
            )

        details_widget.loading = False

    def action_reload(self) -> None:
        tab_id = self.query_one(Tabs).active
        current_tab = Feed(tab_id)
        self.on_tab_switch_load(current_tab, force=True)

    def action_open(self) -> None:
        table = self.query_one('#table', DataTable)
        table_row = table.get_row_at(table.cursor_row)

        if table_row:
            story_id = int(table_row[0])

            target_url = self._stories[story_id].url

            if target_url:
                webbrowser.open(target_url)
            else:
                self.notify('Текущая история не содержит ссылки')

    def action_save(self) -> None:
        table = self.query_one('#table', DataTable)
        table_row = table.get_row_at(table.cursor_row)

        if table_row:
            story_id = int(table_row[0])
            story = self._stories[story_id]

            if not story.text:
                self.notify('Для чтения данной истории откройте браузер кнопкой o')
                return

            title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', story.title)
            saved_story = self._saved_stories_path / f'{title}.txt'

            try:
                with saved_story.open('w', encoding='utf-8') as f:
                    f.write(story.text)
            except OSError:
                self.notify(
                    'Ошибка записи истории. Проверьте наличие папки saved-stories',
                    severity='error',
                )

    def action_quit(self) -> None:
        self.app.exit()
