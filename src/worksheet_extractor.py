"""
Worksheet extractor module for Tableau workbook files.
Extracts worksheet information from .twb files.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from pathlib import Path
import logging


class WorksheetExtractor:
    """Extracts worksheet information from Tableau workbook files."""

    def __init__(self, file_path: str) -> None:
        """Initialize the worksheet extractor.

        Args:
            file_path: Path to the Tableau workbook file (.twb)
        """
        self.file_path = Path(file_path)
        self.logger = logging.getLogger(__name__)

    def extract_worksheets(self) -> List[Dict[str, Any]]:
        """Extract all worksheets from the Tableau workbook.

        Returns:
            List of dictionaries containing worksheet information
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Tableau file not found: {self.file_path}")

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            worksheets = []
            worksheet_elements = root.findall(".//worksheet")

            for idx, worksheet in enumerate(worksheet_elements, 1):
                worksheet_info = self._parse_worksheet(worksheet=worksheet, index=idx)
                if worksheet_info:
                    worksheets.append(worksheet_info)

            return worksheets

        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def _parse_worksheet(self, worksheet: ET.Element, index: int) -> Dict[str, Any]:
        """Parse a single worksheet element.

        Args:
            worksheet: XML element representing a worksheet
            index: Index of the worksheet

        Returns:
            Dictionary containing worksheet information
        """
        name = worksheet.get("name", f"Worksheet {index}")

        # Get additional worksheet attributes if available
        view_port = worksheet.find(".//view/datasourcedata")
        has_data = view_port is not None

        return {
            "index": index,
            "name": name,
            "has_data": has_data,
        }

    def print_worksheets(self, worksheets: List[Dict[str, Any]]) -> None:
        """Print worksheets in a formatted way to console.

        Args:
            worksheets: List of worksheet dictionaries
        """
        if not worksheets:
            print("No worksheets found.")
            return

        print(f"\n{len(worksheets)} Worksheet(s)")
        print()
        print("WORKSHEET NAME")
        print("-" * 50)

        for worksheet in worksheets:
            print(f"{worksheet['index']:<3} {worksheet['name']}")

    def run(self) -> List[Dict[str, Any]]:
        """Run the worksheet extraction process.

        Returns:
            List of worksheet dictionaries
        """
        worksheets = self.extract_worksheets()
        self.print_worksheets(worksheets=worksheets)
        return worksheets


def extract_worksheets_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Utility function to extract worksheets from a Tableau workbook file.

    Args:
        file_path: Path to the Tableau workbook file

    Returns:
        List of worksheet dictionaries
    """
    extractor = WorksheetExtractor(file_path=file_path)
    return extractor.run()
