from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import maxitrol_g6r_h4t_protocol

APP_ROOT = Path(__file__).resolve().parents[1]
TEST_PACKAGE = "_maxitrol_test_app"


class StubApp:
    def __init__(self) -> None:
        self.logs: list[str] = []

    async def on_init(self) -> None:
        return None

    def log(self, message: str) -> None:
        self.logs.append(message)


class StubDevice(StubApp):
    def __init__(self) -> None:
        super().__init__()
        self.data: dict[str, Any] = {}
        self.capability_listeners: dict[str, Any] = {}

    def get_data(self) -> dict[str, Any]:
        return self.data

    def register_capability_listener(self, capability: str, listener: Any) -> None:
        self.capability_listeners[capability] = listener


class StubDriver(StubApp):
    def __init__(self) -> None:
        super().__init__()
        self.errors: list[tuple[str, Exception]] = []

    def error(self, message: str, error: Exception) -> None:
        self.errors.append((message, error))


class StubPairSession:
    pass


def install_homey_stubs() -> None:
    homey = ModuleType("homey")
    homey.__path__ = []  # type: ignore[attr-defined]

    app = ModuleType("homey.app")
    app.App = StubApp  # type: ignore[attr-defined]
    device = ModuleType("homey.device")
    device.Device = StubDevice  # type: ignore[attr-defined]
    driver = ModuleType("homey.driver")
    driver.Driver = StubDriver  # type: ignore[attr-defined]
    pair_session = ModuleType("homey.pair_session")
    pair_session.PairSession = StubPairSession  # type: ignore[attr-defined]

    homey.app = app  # type: ignore[attr-defined]
    homey.device = device  # type: ignore[attr-defined]
    homey.driver = driver  # type: ignore[attr-defined]
    homey.pair_session = pair_session  # type: ignore[attr-defined]

    sys.modules.update(
        {
            "homey": homey,
            "homey.app": app,
            "homey.device": device,
            "homey.driver": driver,
            "homey.pair_session": pair_session,
        }
    )


def _install_test_package() -> None:
    package_paths = {
        TEST_PACKAGE: APP_ROOT,
        f"{TEST_PACKAGE}.drivers": APP_ROOT / "drivers",
        f"{TEST_PACKAGE}.drivers.fireplace": APP_ROOT / "drivers" / "fireplace",
    }
    for name, path in package_paths.items():
        package = ModuleType(name)
        package.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = package

    sys.modules[f"{TEST_PACKAGE}.maxitrol_g6r_h4t_protocol"] = (
        maxitrol_g6r_h4t_protocol
    )


def load_app_module(relative_path: str, module_suffix: str) -> ModuleType:
    install_homey_stubs()
    _install_test_package()

    module_name = f"{TEST_PACKAGE}.{module_suffix}"
    sys.modules.pop(module_name, None)
    spec = spec_from_file_location(module_name, APP_ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {relative_path}")

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
