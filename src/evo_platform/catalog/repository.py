from typing import Protocol

from evo_platform.catalog.models import CatalogEntry


class CatalogRepository(Protocol):
    async def publish(self, entry: CatalogEntry) -> CatalogEntry: ...
    async def get(self, entry_id: str) -> CatalogEntry | None: ...


class InMemoryCatalogRepository:
    def __init__(self) -> None:
        self._entries: dict[str, CatalogEntry] = {}

    async def publish(self, entry: CatalogEntry) -> CatalogEntry:
        self._entries[entry.id] = entry
        return entry

    async def get(self, entry_id: str) -> CatalogEntry | None:
        return self._entries.get(entry_id)
