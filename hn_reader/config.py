from dataclasses import dataclass


@dataclass
class Config:
    base_url: str
    user_agent: str
    timeout: float
    connect: float
    max_connection: int
    timeout_retries: list[float]
    top_comments_load_limit: int
