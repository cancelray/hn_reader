import os
import re
import webbrowser
from pathlib import Path
from typing import Any

from rich.text import Text
from textual import events, work
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Markdown,
    Tab,
    Tabs,
)
from textual.widgets.data_table import CellDoesNotExist

from hn_reader.config import Config
from hn_reader.exceptions import HnException
from hn_reader.models import Comment, Feed, Story
from hn_reader.services import BaseStoriesService
from hn_reader.ui.screens.story_modal import StoryModal
from hn_reader.ui.widgets import TableWidget
from hn_reader.ui.widgets.input import InputWidget


class MainScreen(Screen):
    def __init__(
        self, config: Config, stories_service: BaseStoriesService, *args, **kwargs
    ) -> None:
        self.config = config
        self.stories_service = stories_service
        self._stories: dict[int, Story] = {}
        self._comments: list[Comment] = []
        self._rows: list[Any] = []
        self._base_dir: Path = Path(__file__).resolve().parent.parent.parent.parent
        self._current_row: list[Any] = []
        self._load_progress: int = 0
        self._total: int = 0
        super().__init__(*args, **kwargs)

    CSS_PATH = 'styles.tcss'

    BINDINGS = (
        ('r', 'reload', 'Обновить'),
        ('o', 'open', 'Открыть'),
        ('s', 'save', 'Сохранить (только текст)'),
        ('/', 'filter_focus', 'Фильтр'),
        ('←→', '', 'Вкладка'),
        ('q', 'quit', 'Выход'),
    )

    def compose(self) -> ComposeResult:
        self._total = self.config.load_limit

        yield Header()
        yield Tabs(Tab('Top', id='top'), Tab('New', id='new'), Tab('Best', id='best'))
        yield InputWidget(
            id='filter-input', placeholder='Для фильтрации историй нажмите /'
        )
        with Horizontal(id='horizontal-content'):
            yield TableWidget(id='table-widget')
            with VerticalScroll(id='vertical-scroll-markdown'):
                yield Markdown('Выберите историю для загрузки', id='details')
        yield Label('Ожидание загрузки', id='status-label')
        yield Footer()

    def _filter_table(self, value: str) -> None:
        table = self.query_one('#table', DataTable)
        table.clear()

        clear_value = value.strip().lower()

        for row in self._rows:
            if clear_value in str(row[1]).lower():
                table.add_row(*row)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._filter_table(event.value)

    @work(exclusive=True)
    async def load_feed_worker(self, feed: Feed, force: bool = False) -> None:
        table = self.query_one('#table', DataTable)
        table.clear()

        md_widget = self.query_one('#details', Markdown)
        md_widget.update('Выберите историю для загрузки')

        self._load_progress = 0
        self._rows = []

        status_label = self.query_one('#status-label', Label)
        status_label.update(f'Загружено {self._load_progress}/{self._total}')

        table.add_row('...', 'Загрузка данных...', key='loader')

        try:
            async for story in self.stories_service.load_feed(
                feed, limit=self.config.load_limit, force=force
            ):
                self._stories[story.id] = story
                crop_title = Text(story.title, no_wrap=True, overflow='ellipsis')

                if 'loader' in table.rows:
                    table.remove_row('loader')

                key = table.add_row(
                    story.id,
                    crop_title,
                    story.score,
                    story.comments_count,
                    story.age,
                    key=str(story.id),
                )

                self._rows.append(table.get_row(key))

                table.add_row('...', 'Загрузка данных', key='loader')

                self._load_progress += 1
                status_label.update(f'Загружено {self._load_progress}/{self._total}')
        except HnException as e:
            self.notify(e.message)
            status_label.update('Ошибка загрузки')
            self._load_progress = 0
        else:
            status_label.update('Загружено')
            self._load_progress = 0
        finally:
            if 'loader' in table.rows:
                table.remove_row('loader')

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        tab_id = event.tab.id
        current_tab = Feed(tab_id)
        self.load_feed_worker(current_tab)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one('#table', DataTable)
        row = table.get_row(event.row_key)

        if row == self._current_row:
            return

        self._current_row = row

        details_widget = self.query_one('#details', Markdown)
        details_widget.loading = True

        story_id = int(row[0])
        story = self._stories[story_id]

        self._comments = []

        title = f'{story.title}'
        author = f'Author: {story.author}'
        score = f'Score: {story.score}'
        comments_count = f'Comments: {story.comments_count}'
        posted = f'Posted: {story.created_at:%Y-%m-%d}'
        content = story.text
        if story.url:
            url = f'URL: {story.url}'
            content = url

        try:
            comments = await self.stories_service.load_comments(
                story, self.config.top_comments_load_limit
            )

            comments_title = '-----Top comments-----'
            comments_block = 'No comments yet'

            if comments:
                self._comments = comments.copy()
                format_comments: list[str] = []

                for comment in comments:
                    format_comments.append(f'{comment.author}: {comment.text}')

                comments_block = '\\\n'.join(format_comments)

            details_widget.update(
                f'{title}\n\n{author}\\\n{score}\\\n{comments_count}\\\n{posted}\\\n{content}\n\n{comments_title}\n\n{comments_block}'
            )

            vertical_widget = self.query_one(
                '#vertical-scroll-markdown', VerticalScroll
            )
            vertical_widget.scroll_home(animate=False)
        except HnException as e:
            self.notify(e.message)

        details_widget.loading = False

    def action_reload(self) -> None:
        tab_id = self.query_one(Tabs).active
        current_tab = Feed(tab_id)
        self.load_feed_worker(current_tab, force=True)

    def action_open(self) -> None:
        table = self.query_one('#table', DataTable)
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        except CellDoesNotExist:
            return

        if row_key.value and row_key.value.isdigit():
            story_id = int(row_key.value)

            target_url = self._stories[story_id].url

            if target_url:
                webbrowser.open(target_url)
            else:
                story = self._stories[story_id]
                count_of_top_comments = self.config.top_comments_load_limit

                self.app.push_screen(
                    StoryModal(story, self._comments, count_of_top_comments)
                )

    def action_save(self) -> None:
        table = self.query_one('#table', DataTable)
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        except CellDoesNotExist:
            return

        if row_key.value and row_key.value.isdigit():
            story_id = int(row_key.value)
            story = self._stories[story_id]

            if not story.text:
                self.notify('Для чтения данной истории откройте браузер кнопкой o')
                return

            title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', story.title)

            try:
                if not (self._base_dir / 'saved-stories').is_dir():
                    os.makedirs(self._base_dir / 'saved-stories')

                saved_story = self._base_dir / 'saved-stories' / f'{title}.txt'

                with saved_story.open('w', encoding='utf-8') as f:
                    f.write(story.text)
                    self.notify(
                        f'История {story.title} сохранена в папке saved-stories',
                    )
            except OSError:
                self.notify(
                    'Ошибка записи истории. Попробуйте снова.',
                    severity='error',
                )

    def on_key(self, event: events.Key) -> None:
        if event.key == 'escape':
            md_widget = self.query_one('#details', Markdown)
            md_widget.update('Выберите историю для загрузки')
            event.stop()

        if event.key == 'left' or event.key == 'right':
            tab_widget = self.query_one(Tabs)

            match event.key:
                case 'left':
                    tab_widget.action_previous_tab()
                case 'right':
                    tab_widget.action_next_tab()

            event.stop()

    def action_filter_focus(self) -> None:
        filter_input = self.query_one('#filter-input', InputWidget)
        filter_input.focus()

    def action_quit(self) -> None:
        self.app.exit()
