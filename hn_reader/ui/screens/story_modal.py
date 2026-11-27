from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Markdown

from hn_reader.models import Comment, Story


class StoryModal(ModalScreen[str]):
    def __init__(
        self,
        story: Story,
        comments: list[Comment],
        count_of_top_comments: int,
        *args,
        **kwargs,
    ) -> None:
        self._story = story
        self._comments = comments
        self._count_of_top_comments = count_of_top_comments
        super().__init__(*args, **kwargs)

    BINDINGS = (('escape', 'close', 'Закрыть историю'),)

    def compose(self) -> ComposeResult:
        info = '---Для выхода нажмите esc---'
        title = f'{self._story.title}'
        author = f'Author: {self._story.author}'
        content = self._story.text

        comments_title = f'-----Top {self._count_of_top_comments} comments-----'
        comments_block = 'No comments yet'

        if self._comments:
            format_comments: list[str] = []

            for comment in self._comments:
                format_comments.append(f'{comment.author}: {comment.text}')

            comments_block = '\n\n'.join(format_comments)

        with VerticalScroll(id='modal-container'):
            yield Markdown(
                f'{info}\n\n\n{title}\\\n{author}\n\n{content}\n\n{comments_title}\n\n{comments_block}\n\n\n{info}',
                id='md-text',
            )

    def action_close(self) -> None:
        self.dismiss()
