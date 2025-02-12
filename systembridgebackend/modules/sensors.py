"""System Bridge: Sensors"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from typing import Optional

import psutil
from systembridgeshared.base import Base
from systembridgeshared.common import make_key
from systembridgeshared.database import Database
from systembridgeshared.models.database_data_sensors import Sensors as DatabaseModel

from .base import ModuleUpdateBase


class Sensors(Base):
    """Sensors"""

    def fans(self) -> Optional[dict]:
        """Get fans"""
        if not hasattr(psutil, "sensors_fans"):
            return None
        return psutil.sensors_fans()  # type: ignore

    def temperatures(self) -> Optional[dict]:
        """Get temperatures"""
        if not hasattr(psutil, "sensors_temperatures"):
            return None
        return psutil.sensors_temperatures()  # type: ignore

    def windows_sensors(self) -> Optional[dict]:
        """Get windows sensors"""
        if sys.platform != "win32":
            return None

        try:
            # Import here to not raise error when importing file on linux
            # pylint: disable=import-error, import-outside-toplevel
            from systembridgewindowssensors import get_windowssensors_path
        except (ImportError, ModuleNotFoundError) as error:
            self._logger.error("Windows sensors not found: %s", error)
            return None

        path = get_windowssensors_path()

        self._logger.debug("Windows sensors path: %s", path)
        try:
            with subprocess.Popen(
                [path],
                stdout=subprocess.PIPE,
            ) as pipe:
                result = pipe.communicate()[0].decode()
            self._logger.debug("Windows sensors result: %s", result)
        except Exception as error:  # pylint: disable=broad-except
            self._logger.error(
                "Windows sensors error: %s (%s)",
                error,
                path,
            )
            return None

        try:
            return json.loads(result)
        except json.decoder.JSONDecodeError as error:
            self._logger.error(error)
            return None


class SensorsUpdate(ModuleUpdateBase):
    """Sensors Update"""

    def __init__(
        self,
        database: Database,
    ) -> None:
        """Initialize"""
        super().__init__(database)
        self._sensors = Sensors()

    async def update_fans(self) -> None:
        """Update Fan Sensors"""
        if data := self._sensors.fans():
            for key, value in data.items():
                for item in value:
                    for subkey, subvalue in item._asdict().items():
                        self._database.update_data(
                            DatabaseModel,
                            DatabaseModel(
                                key=f"fans_{key}_{subkey}",
                                type=subkey,
                                name=subkey,
                                hardware_type=key,
                                hardware_name=key,
                                value=subvalue,
                            ),
                        )

    async def update_temperatures(self) -> None:
        """Update Temperature Sensors"""
        if data := self._sensors.temperatures():
            for key, value in data.items():
                for item in value:
                    for subkey, subvalue in item._asdict().items():
                        self._database.update_data(
                            DatabaseModel,
                            DatabaseModel(
                                key=f"temperatures_{key}_{subkey}",
                                type=subkey,
                                name=subkey,
                                hardware_type=key,
                                hardware_name=key,
                                value=subvalue,
                            ),
                        )

    async def update_windows_sensors(self) -> None:
        """Update Windows Sensors"""
        if not (data := self._sensors.windows_sensors()):
            return
        if "hardware" in data and data["hardware"] is not None:
            for hardware in data["hardware"]:
                key_hardware = (
                    make_key(f"_{hardware['name']}") if "name" in hardware else None
                )
                for sensor in hardware["sensors"] or []:
                    key_sensor_name = make_key(sensor["name"])
                    key_sensor_type = make_key(sensor["type"])

                    self._database.update_data(
                        DatabaseModel,
                        DatabaseModel(
                            key=f"windows_hardware{key_hardware}_{key_sensor_name}_{key_sensor_type}",
                            type=sensor["type"],
                            name=sensor["name"],
                            hardware_type=hardware["type"],
                            hardware_name=hardware["name"],
                            value=sensor["value"] if "value" in sensor else None,
                        ),
                    )

        if "nvidia" in data and data["nvidia"] is not None:
            for sensor, value in data["nvidia"].items():
                if isinstance(value, list):
                    counter = 0
                    for hardware in value:
                        key_hardware = (
                            make_key(f"_{hardware['name']}")
                            if "name" in hardware
                            else None
                        )
                        type_hardware = (
                            hardware["type"] if "type" in hardware else "NVIDIA"
                        )
                        name_hardware = hardware["name"] if "name" in hardware else ""
                        if "DISPLAY" in name_hardware:
                            type_hardware = "Display"
                            name_hardware = (
                                f"Display {name_hardware.split('DISPLAY')[1]}"
                            )
                        for subkey, subvalue in hardware.items():
                            self._database.update_data(
                                DatabaseModel,
                                DatabaseModel(
                                    key=f"windows_nvidia{key_hardware}_{sensor}_{counter}_{subkey}",
                                    type=sensor,
                                    name=subkey,
                                    hardware_type=type_hardware,
                                    hardware_name=name_hardware,
                                    value=subvalue,
                                ),
                            )
                        counter += 1
                else:
                    for subkey, subvalue in value.items():
                        self._database.update_data(
                            DatabaseModel,
                            DatabaseModel(
                                key=f"windows_nvidia_{sensor}_{subkey}",
                                type=sensor,
                                name=subkey,
                                hardware_type=value["type"]
                                if "type" in value
                                else "NVIDIA",
                                hardware_name=value["name"]
                                if "name" in value
                                else "NVIDIA",
                                value=subvalue,
                            ),
                        )

    async def update_all_data(self) -> None:
        """Update data"""

        # Clear table in case of hardware changes since last run
        self._database.clear_table(DatabaseModel)
        await asyncio.gather(
            *[
                self.update_fans(),
                self.update_temperatures(),
                self.update_windows_sensors(),
            ]
        )
