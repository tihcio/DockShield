"""
Configuration management for DockShield
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for DockShield"""

    DEFAULT_CONFIG_PATHS = [
        Path.home() / ".config" / "dockshield" / "config.yml",
        Path("/etc/dockshield/config.yml"),
    ]

    DEFAULT_CONFIG = {
        "general": {
            "backup_dir": "/var/backups/dockshield",
            "compression_level": 6,
            "retention_days": 30,
            "max_concurrent_jobs": 2,
            "log_level": "INFO",
            "log_file": "~/.local/share/dockshield/dockshield.log",
        },
        "docker": {
            "socket": "unix:///var/run/docker.sock",
            "api_version": "",
            "timeout": 300,
        },
        "backup": {
            "default_type": "full",
            "include_logs": True,
            "max_log_size": 100,
            "verify_backup": True,
            "exclude_patterns": ["*.tmp", "*.log", ".cache/*"],
        },
        "storage": {
            "local": {
                "enabled": True,
                "path": "/var/backups/dockshield",
            },
        },
        "scheduler": {
            "enabled": False,
            "jobs": [],
        },
        "notifications": {
            "desktop_enabled": True,
            "notify_success": True,
            "notify_failure": True,
            "sound_enabled": True,
        },
        "ui": {
            "theme": "auto",
            "language": "en",
            "window": {
                "width": 1200,
                "height": 800,
                "remember_position": True,
            },
            "refresh_interval": 5,
            "system_tray": True,
            "minimize_to_tray": True,
        },
        "advanced": {
            "debug": False,
            "use_sudo": False,
            "docker_command": "/usr/bin/docker",
            "compression_threads": 4,
            "buffer_size": 8388608,
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration

        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = self.DEFAULT_CONFIG.copy()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file"""
        # If specific path provided, use it
        if self.config_path and self.config_path.exists():
            self._load_from_file(self.config_path)
            return

        # Otherwise, try default paths
        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                self.config_path = path
                self._load_from_file(path)
                return

        # No config file found, use defaults
        logger.info("No configuration file found, using defaults")

    def _load_from_file(self, path: Path) -> None:
        """Load configuration from YAML file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)

            if user_config:
                self._merge_config(user_config)
                logger.info(f"Configuration loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {path}: {e}")
            logger.info("Using default configuration")

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """Merge user configuration with defaults"""
        def merge_dict(base: Dict, update: Dict) -> Dict:
            """Recursively merge dictionaries"""
            result = base.copy()
            for key, value in update.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result

        self.config = merge_dict(self.config, user_config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key: Configuration key (e.g., "general.backup_dir")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation

        Args:
            key: Configuration key (e.g., "general.backup_dir")
            value: Value to set
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save configuration to file

        Args:
            path: Path to save configuration (optional, uses loaded path if not specified)
        """
        save_path = path or self.config_path

        if not save_path:
            save_path = self.DEFAULT_CONFIG_PATHS[0]

        # Create directory if it doesn't exist
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {save_path}: {e}")
            raise

    def expand_path(self, path: str) -> Path:
        """
        Expand path with user home directory

        Args:
            path: Path string (may contain ~)

        Returns:
            Expanded Path object
        """
        return Path(os.path.expanduser(path)).resolve()

    def get_backup_dir(self) -> Path:
        """Get backup directory as Path object"""
        return self.expand_path(self.get("general.backup_dir"))

    def get_log_file(self) -> Path:
        """Get log file path as Path object"""
        log_file = self.expand_path(self.get("general.log_file"))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        return log_file
