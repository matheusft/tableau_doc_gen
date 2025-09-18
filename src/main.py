"""
Main entry point for Tableau documentation generator.
Orchestrates all extraction modules.
"""

import logging
import sys
from pathlib import Path

# Add config directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "config"))

from config_manager import load_config, setup_logging_from_config
from datasource_extractor import extract_datasources_from_file
from table_extractor import extract_tables_from_file


def main() -> None:
    """Main function to orchestrate Tableau workbook analysis."""
    try:
        # Load configuration
        config = load_config()

        # Setup logging
        setup_logging_from_config(config=config)
        logger = logging.getLogger(__name__)

        logger.info("Starting Tableau documentation generator")

        # Extract datasources if enabled
        if config.datasource.enabled:
            logger.info("Extracting datasources...")
            datasources = extract_datasources_from_file(
                file_path=config.tableau.file_path
            )
            logger.info(f"Found {len(datasources)} datasources")

        # Extract tables if enabled
        if config.table.enabled:
            logger.info("Extracting datasource tables...")
            tables = extract_tables_from_file(file_path=config.tableau.file_path)
            logger.info(f"Found {len(tables)} datasource tables")

        logger.info("Documentation generation completed")

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
