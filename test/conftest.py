import importlib
import os
from unittest.mock import Mock

import pytest

from modules.config import ConfigManager


@pytest.fixture(autouse=True, scope="session")
def app_root(tmp_path_factory):
    """Set up a temporary application root with config files and output directories."""
    tmp_path = tmp_path_factory.mktemp("sdcpp-webui")
    config_path = tmp_path / "config.json"
    prompts_path = tmp_path / "prompts.json"

    # output directories
    txt2img_dir = tmp_path / "txt2img"
    txt2img_dir.mkdir()
    img2img_dir = tmp_path / "img2img"
    img2img_dir.mkdir()

    # Initialize default config files
    config = ConfigManager(config_path)
    config.update_settings({
        "txt2img_dir": str(txt2img_dir),
        "img2img_dir": str(img2img_dir),
    })

    # Export environment variables for the application to use
    os.environ['SD_WEBUI_CONFIG_PATH'] = str(config_path)
    os.environ['SD_WEBUI_PROMPTS_PATH'] = str(prompts_path)

    yield tmp_path

    del os.environ['SD_WEBUI_CONFIG_PATH']
    del os.environ['SD_WEBUI_PROMPTS_PATH']


@pytest.fixture
def mocker(monkeypatch):
    """Minimal pytest-mock compatible fixture for simple patch calls."""

    class Mocker:
        def patch(self, target, *args, **kwargs):
            replacement = kwargs.pop("new", None)
            if replacement is None:
                replacement = Mock(*args, **kwargs)

            parts = target.split(".")
            module = None
            attr_parts = []
            for split_at in range(len(parts) - 1, 0, -1):
                module_name = ".".join(parts[:split_at])
                try:
                    module = importlib.import_module(module_name)
                except ModuleNotFoundError:
                    continue
                attr_parts = parts[split_at:]
                break

            if module is None or not attr_parts:
                raise ModuleNotFoundError(target)

            parent = module
            for attr_name in attr_parts[:-1]:
                parent = getattr(parent, attr_name)

            monkeypatch.setattr(parent, attr_parts[-1], replacement)
            return replacement

    return Mocker()


@pytest.fixture(autouse=True)
def sd_options_mock(request, mocker):
    if request.path.name == "test_sd_interface.py":
        return

    mocker.patch("modules.utils.sd_interface.SDOptionsCache")
    mocker.patch(
        "modules.utils.sd_interface.exe_name",
        new=lambda mode="cli": f"sd-{mode}",
    )
