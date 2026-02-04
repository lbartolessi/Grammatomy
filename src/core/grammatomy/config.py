import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Absolute path to the project root
# src/core/grammatomy/config.py -> parents[3] = root
PROJECT_ROOT = Path(__file__).parents[3]
CONFIG_FILE = PROJECT_ROOT / "config.yaml"


class AppConfig:
    """
    Singleton configuration manager ensuring Model Sovereignty.
    Loads settings from config.yaml and resolves local paths.
    """

    _instance = None
    _data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        if not CONFIG_FILE.exists():
            raise FileNotFoundError(
                f"Critical: Configuration file missing at {CONFIG_FILE}"
            )

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    @property
    def models_path(self) -> Path:
        """Returns the absolute path to the local models directory."""
        rel_path = self._data.get("system", {}).get("resources_path", "models")
        return PROJECT_ROOT / rel_path

    def get_models_for_engine(self, engine: str, lang: str) -> List[str]:
        """Retrieves available local models for a specific engine and language."""
        engines_conf = self._data.get("engines", {})
        return engines_conf.get(engine, {}).get("languages", {}).get(lang, [])


# Global instance
config = AppConfig()
