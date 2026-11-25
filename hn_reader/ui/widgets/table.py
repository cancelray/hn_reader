from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import DataTable


class TableWidget(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield DataTable(id='table')

    def on_mount(self) -> None:
        table = self.query_one('#table', DataTable)
        table.zebra_stripes = True
        table.cursor_type = 'row'

        table.add_column('#', width=10, key='id')
        table.add_column('Title', width=25, key='title')
        table.add_column('Score', width=5, key='score')
        table.add_column('Cmts', width=5, key='cmnts')
        table.add_column('Age', width=5, key='age')
