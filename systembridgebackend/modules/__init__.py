"""System Bridge: Modules"""
import asyncio
from collections.abc import Awaitable, Callable

from systembridgeshared.base import Base
from systembridgeshared.database import Database

from .battery import BatteryUpdate
from .cpu import CPUUpdate
from .disk import DiskUpdate
from .display import DisplayUpdate
from .gpu import GPUUpdate
from .memory import MemoryUpdate
from .network import NetworkUpdate
from .processes import ProcessesUpdate
from .sensors import SensorsUpdate
from .system import SystemUpdate

MODULES = [
    "battery",
    "cpu",
    "disk",
    "display",
    "gpu",
    "media",
    "memory",
    "network",
    "processes",
    "sensors",
    "system",
]


class Update(Base):
    """Modules Update"""

    def __init__(
        self,
        database: Database,
        updated_callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Initialize"""
        super().__init__()
        self._database = database  # pylint: disable=duplicate-code
        self.updated_callback = updated_callback

        self._classes = [
            {"name": "battery", "cls": BatteryUpdate(self._database)},
            {"name": "disk", "cls": DiskUpdate(self._database)},
            {"name": "system", "cls": SystemUpdate(self._database)},
        ]
        self._classes_frequent = [
            {"name": "cpu", "cls": CPUUpdate(self._database)},
            {"name": "display", "cls": DisplayUpdate(self._database)},
            {"name": "gpu", "cls": GPUUpdate(self._database)},
            {"name": "memory", "cls": MemoryUpdate(self._database)},
            {"name": "network", "cls": NetworkUpdate(self._database)},
            {"name": "processes", "cls": ProcessesUpdate(self._database)},
        ]

    async def _update(
        self,
        class_obj: dict,
    ) -> None:
        """Update"""
        await class_obj["cls"].update_all_data()
        await self.updated_callback(class_obj["name"])

    async def update_data(self) -> None:
        """Update Data"""
        self._logger.info("Update data")

        tasks = [self._update(cls) for cls in self._classes]
        await asyncio.gather(*tasks)

        self._logger.info("Finished updating data")

    async def update_frequent_data(self) -> None:
        """Update Data"""
        self._logger.info("Update frequent data")

        sensors_update = SensorsUpdate(self._database)
        await sensors_update.update_all_data()
        await self.updated_callback("sensors")

        tasks = [self._update(cls) for cls in self._classes_frequent]
        await asyncio.gather(*tasks)

        self._logger.info("Finished updating frequent data")
