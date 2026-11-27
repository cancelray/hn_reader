from textual import events
from textual.widgets import DataTable, Input


class InputWidget(Input):
    def on_key(self, event: events.Key) -> None:
        if event.key == 'escape':
            self.screen.query_one('#table', DataTable).focus()
            self.value = ''
            event.stop()
