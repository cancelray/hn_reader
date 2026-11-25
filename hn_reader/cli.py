from hn_reader import Config
from hn_reader.api import HttpxProvider
from hn_reader.api.base_provider import BaseProvider
from hn_reader.services import BaseStoriesService, StoriesService
from hn_reader.ui import HnApp


def create_app() -> HnApp:
    config: Config = Config(
        base_url='https://hacker-news.firebaseio.com/v0/',
        user_agent='MyHNClient/1.0',
        timeout=10.0,
        connect=5.0,
        max_connection=10,
        timeout_retries=[0.5, 1.0],
        top_comments_load_limit=5,
    )

    httpx_provider: BaseProvider = HttpxProvider(config)
    stories_service: BaseStoriesService = StoriesService(httpx_provider)

    return HnApp(config, stories_service, httpx_provider)


def run():
    app = create_app()
    app.run()
