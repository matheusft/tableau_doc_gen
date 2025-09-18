"""
Configuration manager for Tableau documentation generator.
Handles loading and validation of configuration files.
"""

import logging
import yaml
from pathlib import Path
from munch import Munch


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_path: str = "config/config.yaml") -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self._config: Munch = None

    def load_config(self) -> Munch:
        """Load configuration from YAML file.

        Returns:
            Configuration object as Munch

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            yaml.YAMLError: If YAML parsing fails
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, "r") as f:
                config_data = yaml.safe_load(f)

            self._config = Munch.fromDict(config_data)
            self._validate_config()
            return self._config

        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML configuration: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration: {e}")
            raise

    def _validate_config(self) -> None:
        """Validate required configuration sections and keys."""
        required_sections = ["tableau", "logging"]

        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate tableau section
        if "file_path" not in self._config.tableau:
            raise ValueError("Missing required key 'file_path' in tableau section")

        # Validate logging section
        if "level" not in self._config.logging:
            raise ValueError("Missing required key 'level' in logging section")

    def get_config(self) -> Munch:
        """Get the loaded configuration.

        Returns:
            Configuration object as Munch

        Raises:
            RuntimeError: If configuration hasn't been loaded yet
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config

    def setup_logging(self) -> None:
        """Setup logging configuration based on config settings."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")

        log_level = self._config.logging.level.upper()
        log_format = getattr(
            self._config.logging,
            "format",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        logging.basicConfig(level=getattr(logging, log_level), format=log_format)


def load_config(config_path: str = "config/config.yaml") -> Munch:
    """Utility function to load configuration.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration object as Munch
    """
    config_manager = ConfigManager(config_path=config_path)
    return config_manager.load_config()


def setup_logging_from_config(config: Munch) -> None:
    """Setup logging from configuration object.

    Args:
        config: Configuration object containing logging settings
    """
    log_level = config.logging.level.upper()
    log_format = getattr(
        config.logging, "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logging.basicConfig(level=getattr(logging, log_level), format=log_format)
