class HnException(Exception):
    def __init__(self, message: str, status_code: int | None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class HnTimeoutError(HnException): ...


class HnNetworkError(HnException): ...


class HnServerError(HnException): ...
