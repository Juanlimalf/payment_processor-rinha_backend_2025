import httpx


class HttpClient:
    __slots__ = ("http_client",)

    def __init__(self):
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=500, max_keepalive_connections=100),
            timeout=httpx.Timeout(10.0, connect=10.0, read=10.0, write=10.0),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )

    def get_client(self):
        return self.http_client
