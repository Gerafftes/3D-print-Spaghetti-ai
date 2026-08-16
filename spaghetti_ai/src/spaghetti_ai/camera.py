from __future__ import annotations

from collections.abc import Callable

import requests


class SnapshotClient:
    """Fetches independent snapshots so every loop naturally reconnects."""

    def __init__(
        self,
        url: str,
        timeout_seconds: float,
        getter: Callable = requests.get,
    ) -> None:
        self._url = url
        self._timeout_seconds = timeout_seconds
        self._getter = getter

    def fetch(self) -> bytes:
        response = self._getter(self._url, timeout=self._timeout_seconds)
        response.raise_for_status()
        if not response.content:
            raise ValueError("Camera returned an empty response")
        return response.content
