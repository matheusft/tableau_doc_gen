"""
Table extractor module for Tableau workbook files.
Extracts datasource tables information from .twb files.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from pathlib import Path
import logging


class TableExtractor:
    """Extracts datasource table information from Tableau workbook files."""

    def __init__(self, file_path: str) -> None:
        """Initialize the table extractor.

        Args:
            file_path: Path to the Tableau workbook file (.twb)
        """
        self.file_path = Path(file_path)
        self.logger = logging.getLogger(__name__)

    def extract_datasource_tables(self) -> List[Dict[str, Any]]:
        """Extract all datasource tables from the Tableau workbook.

        Returns:
            List of dictionaries containing datasource table information
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Tableau file not found: {self.file_path}")

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            tables = []
            datasource_elements = root.findall(".//datasource")

            for datasource in datasource_elements:
                datasource_caption = datasource.get("caption", "")

                # Skip parameter datasources
                if datasource.get("name", "").lower() == "parameters":
                    continue

                # Find relation elements within this datasource
                relation_elements = datasource.findall(".//relation[@type='table']")

                for relation in relation_elements:
                    table_info = self._parse_relation(
                        relation=relation, datasource_caption=datasource_caption
                    )
                    if table_info:
                        tables.append(table_info)

            # Remove duplicates based on table name and datasource caption
            unique_tables = []
            seen_combinations = set()

            for table in tables:
                key = (table["table_name"], table["datasource_caption"])
                if key not in seen_combinations:
                    unique_tables.append(table)
                    seen_combinations.add(key)

            # Add index to unique tables
            for idx, table in enumerate(unique_tables, 1):
                table["index"] = idx

            return unique_tables

        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def _parse_relation(
        self, relation: ET.Element, datasource_caption: str
    ) -> Dict[str, Any]:
        """Parse a single relation element to extract table information.

        Args:
            relation: XML element representing a table relation
            datasource_caption: Caption of the parent datasource

        Returns:
            Dictionary containing table information or None if invalid
        """
        table_name = relation.get("name", "")
        table_attr = relation.get("table", "")

        if not table_name:
            return None

        # Filter out generic sheet names and invalid table names
        if self._is_invalid_table_name(table_name=table_name):
            return None

        # Clean up table name - remove special characters like $, [], etc.
        clean_table_name = table_name
        if clean_table_name.endswith(".csv"):
            clean_table_name = clean_table_name[:-4]  # Remove .csv extension

        return {
            "table_name": clean_table_name,
            "datasource_caption": datasource_caption,
            "raw_table_attr": table_attr,
        }

    def _is_invalid_table_name(self, table_name: str) -> bool:
        """Check if a table name should be filtered out.

        Args:
            table_name: Name of the table to validate

        Returns:
            True if the table name should be filtered out, False otherwise
        """
        # Convert to lowercase for case-insensitive comparison
        lower_name = table_name.lower()

        # Filter out generic Excel sheet names
        generic_sheet_patterns = [
            "sheet1",
            "sheet2",
            "sheet3",
            "sheet4",
            "sheet5",
            "sheet 1",
            "sheet 2",
            "sheet 3",
            "sheet 4",
            "sheet 5",
        ]

        if lower_name in generic_sheet_patterns:
            return True

        # Filter out empty or very short names
        if len(table_name.strip()) < 2:
            return True

        return False

    def print_tables(self, tables: List[Dict[str, Any]]) -> None:
        """Print datasource tables in a formatted way to console.

        Args:
            tables: List of table dictionaries
        """
        if not tables:
            print("No datasource tables found.")
            return

        print(f"\n{len(tables)} Table(s) found:\n")
        print(
            "DATASOURCE TABLE".ljust(25)
            + "DATASOURCE CAPTION".ljust(25)
            + "DATABASE NAME"
        )
        print("-" * 75)

        for table in tables:
            table_name = table["table_name"]
            datasource_caption = table["datasource_caption"]
            # Use datasource caption as database name for display
            database_name = datasource_caption

            print(
                f"{table['index']:<3} {table_name:<21}"
                f"{datasource_caption:<24} {database_name}"
            )

    def run(self) -> List[Dict[str, Any]]:
        """Run the table extraction process.

        Returns:
            List of table dictionaries
        """
        tables = self.extract_datasource_tables()
        self.print_tables(tables=tables)
        return tables


def extract_tables_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Utility function to extract datasource tables from a Tableau workbook file.

    Args:
        file_path: Path to the Tableau workbook file

    Returns:
        List of table dictionaries
    """
    extractor = TableExtractor(file_path=file_path)
    return extractor.run()
