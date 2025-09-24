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
from worksheet_extractor import extract_worksheets_from_file
from dashboard_extractor import extract_dashboards_from_file
from tableau_fields_analyzer import analyze_tableau_fields
from field_dependencies_extractor import extract_field_dependencies
from field_dependencies_network import create_field_dependencies_network


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

        # Extract worksheets if enabled
        if (
            hasattr(config.table, "extract_worksheets")
            and config.table.extract_worksheets
        ):
            logger.info("Extracting worksheets...")
            worksheets = extract_worksheets_from_file(
                file_path=config.tableau.file_path
            )
            logger.info(f"Found {len(worksheets)} worksheets")

        # Extract dashboards if enabled
        if (
            hasattr(config.table, "extract_dashboards")
            and config.table.extract_dashboards
        ):
            logger.info("Extracting dashboards...")
            dashboards = extract_dashboards_from_file(
                file_path=config.tableau.file_path
            )
            logger.info(f"Found {len(dashboards)} dashboards")

        # Analyze field usage
        logger.info("Analyzing field usage...")
        field_results = analyze_tableau_fields(file_path=config.tableau.file_path)
        used_count = len(field_results.get("used", []))
        unused_count = len(field_results.get("unused", []))
        logger.info(f"Found {used_count} fields used, {unused_count} fields unused")

        # Extract field dependencies
        logger.info("Extracting field dependencies...")
        dependencies = extract_field_dependencies(file_path=config.tableau.file_path)
        logger.info(f"Found {len(dependencies)} field dependencies")

        # Create field dependencies network visualization
        logger.info("Creating field dependencies network visualization...")
        network_graph = create_field_dependencies_network(
            file_path=config.tableau.file_path,
            output_dir="output",
            save_filename="field_dependencies_network.png",
        )
        logger.info(
            f"Network visualization created with {network_graph.number_of_nodes()} nodes "
            f"and {network_graph.number_of_edges()} edges"
        )

        logger.info("Documentation generation completed")

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
