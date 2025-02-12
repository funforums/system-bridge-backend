"""System Bridge: Data"""
import asyncio
import platform
from collections.abc import Awaitable, Callable
from threading import Thread

from systembridgeshared.base import Base
from systembridgeshared.database import Database

from .modules import Update


class UpdateThread(Thread):
    """Update thread"""

    def __init__(
        self,
        database: Database,
        updated_callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Initialize"""
        super().__init__()
        self._database = database
        self._updated_callback = updated_callback
        self._update = Update(self._database, self._updated_callback)

    def run(self) -> None:
        """Run"""
        asyncio.run(self._update.update_data())


class UpdateEventsThread(Thread):
    """Update events thread"""

    def __init__(
        self,
        database: Database,
        updated_callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Initialize"""
        super().__init__()

        if platform.system() != "Windows":
            return

        from .modules.media import (  # pylint: disable=import-error, import-outside-toplevel
            Media,
        )

        self._media = Media(
            database,
            updated_callback,
        )

    def run(self) -> None:
        """Run"""
        if platform.system() != "Windows":
            return

        asyncio.run(self._media.update_media_info())


class UpdateFrequentThread(Thread):
    """Update frequent thread"""

    def __init__(
        self,
        database: Database,
        updated_callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Initialize"""
        super().__init__()
        self._database = database
        self._updated_callback = updated_callback
        self._update = Update(self._database, self._updated_callback)

    def run(self) -> None:
        """Run"""
        asyncio.run(self._update.update_frequent_data())


class Data(Base):
    """Data"""

    def __init__(
        self,
        database: Database,
        updated_callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Initialize"""
        super().__init__()
        self._database = database
        self._updated_callback = updated_callback

    def request_update_data(self) -> None:
        """Request update data"""
        thread = UpdateThread(
            self._database,
            self._updated_callback,
        )
        thread.start()

    def request_update_events_data(self) -> None:
        """Request update events data"""
        thread = UpdateEventsThread(
            self._database,
            self._updated_callback,
        )
        thread.start()

    def request_update_frequent_data(self) -> None:
        """Request update frequent data"""
        thread = UpdateFrequentThread(
            self._database,
            self._updated_callback,
        )
        thread.start()
