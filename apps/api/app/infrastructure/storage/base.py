from typing import BinaryIO, Protocol


class StorageProvider(Protocol):
    """Protocol for persisting audio recordings, transcripts, and avatar media."""

    async def put_object(self, path: str, data: BinaryIO, content_type: str) -> str:
        ...

    async def get_object(self, path: str) -> bytes | None:
        ...

    async def delete_object(self, path: str) -> bool:
        ...

    async def get_url(self, path: str) -> str:
        ...
