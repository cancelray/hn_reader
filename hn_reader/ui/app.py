from textual.app import App

from hn_reader.api import BaseProvider
from hn_reader.config import Config
from hn_reader.services import BaseStoriesService

from .screens import MainScreen


class HnApp(App):
    def __init__(
        self,
        config: Config,
        stories_service: BaseStoriesService,
        httpx_provider: BaseProvider,
        *args,
        **kwargs,
    ):
        self.config = config
        self.stories_service = stories_service
        self.httpx_provider = httpx_provider
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        main_screen = MainScreen(self.config, self.stories_service)
        self.push_screen(main_screen)

    async def on_unmount(self) -> None:
        await self.httpx_provider.close_client()
