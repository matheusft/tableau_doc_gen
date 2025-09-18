"""
Datasource extractor module for Tableau workbook files.
Extracts datasource information from .twb files.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from pathlib import Path
import logging


class DatasourceExtractor:
    """Extracts datasource information from Tableau workbook files."""

    def __init__(self, file_path: str) -> None:
        """Initialize the datasource extractor.

        Args:
            file_path: Path to the Tableau workbook file (.twb)
        """
        self.file_path = Path(file_path)
        self.logger = logging.getLogger(__name__)

    def extract_datasources(self) -> List[Dict[str, Any]]:
        """Extract all datasources from the Tableau workbook.

        Returns:
            List of dictionaries containing datasource information
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Tableau file not found: {self.file_path}")

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            datasources = []
            datasource_elements = root.findall(".//datasource")

            for idx, datasource in enumerate(datasource_elements, 1):
                datasource_info = self._parse_datasource(
                    datasource=datasource, index=idx
                )
                if datasource_info:
                    datasources.append(datasource_info)

            return datasources

        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def _parse_datasource(self, datasource: ET.Element, index: int) -> Dict[str, Any]:
        """Parse a single datasource element.

        Args:
            datasource: XML element representing a datasource
            index: Index of the datasource

        Returns:
            Dictionary containing datasource information
        """
        caption = datasource.get("caption", f"Datasource {index}")
        name = datasource.get("name", "")
        version = datasource.get("version", "")
        inline = datasource.get("inline", "false") == "true"
        has_connection = datasource.get("hasconnection", "true") == "true"

        # Skip parameter datasources (they don't represent actual data sources)
        if name.lower() == "parameters":
            return None

        return {
            "index": index,
            "caption": caption,
            "name": name,
            "version": version,
            "inline": inline,
            "has_connection": has_connection,
        }

    def print_datasources(self, datasources: List[Dict[str, Any]]) -> None:
        """Print datasources in a formatted way to console.

        Args:
            datasources: List of datasource dictionaries
        """
        if not datasources:
            print("No datasources found.")
            return

        print(f"\n{len(datasources)} Data Source(s) found:\n")
        print("DATASOURCE CAPTION")
        print("-" * 50)

        for datasource in datasources:
            print(f"{datasource['index']:<3} {datasource['caption']}")

    def run(self) -> List[Dict[str, Any]]:
        """Run the datasource extraction process.

        Returns:
            List of datasource dictionaries
        """
        datasources = self.extract_datasources()
        filtered_datasources = [ds for ds in datasources if ds is not None]

        # Remove duplicates based on caption
        unique_datasources = []
        seen_captions = set()
        for ds in filtered_datasources:
            if ds["caption"] not in seen_captions:
                unique_datasources.append(ds)
                seen_captions.add(ds["caption"])

        # Reindex the unique datasources
        for i, ds in enumerate(unique_datasources, 1):
            ds["index"] = i

        self.print_datasources(datasources=unique_datasources)
        return unique_datasources


def extract_datasources_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Utility function to extract datasources from a Tableau workbook file.

    Args:
        file_path: Path to the Tableau workbook file

    Returns:
        List of datasource dictionaries
    """
    extractor = DatasourceExtractor(file_path=file_path)
    return extractor.run()
