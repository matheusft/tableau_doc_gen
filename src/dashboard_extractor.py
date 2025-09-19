"""
Dashboard extractor module for Tableau workbook files.
Extracts dashboard information from .twb files.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from pathlib import Path
import logging


class DashboardExtractor:
    """Extracts dashboard information from Tableau workbook files."""

    def __init__(self, file_path: str) -> None:
        """Initialize the dashboard extractor.

        Args:
            file_path: Path to the Tableau workbook file (.twb)
        """
        self.file_path = Path(file_path)
        self.logger = logging.getLogger(__name__)

    def extract_dashboards(self) -> List[Dict[str, Any]]:
        """Extract all dashboards from the Tableau workbook.

        Returns:
            List of dictionaries containing dashboard information
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Tableau file not found: {self.file_path}")

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            dashboards = []
            dashboard_elements = root.findall(".//dashboard")

            for idx, dashboard in enumerate(dashboard_elements, 1):
                dashboard_info = self._parse_dashboard(dashboard=dashboard, index=idx)
                if dashboard_info:
                    dashboards.append(dashboard_info)

            return dashboards

        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def _parse_dashboard(self, dashboard: ET.Element, index: int) -> Dict[str, Any]:
        """Parse a single dashboard element.

        Args:
            dashboard: XML element representing a dashboard
            index: Index of the dashboard

        Returns:
            Dictionary containing dashboard information
        """
        name = dashboard.get("name", f"Dashboard {index}")

        # Get additional dashboard attributes
        sort_zone_enabled = (
            dashboard.get("enable-sort-zone-taborder", "false") == "true"
        )

        # Count the number of zones (layout areas) in the dashboard
        zones = dashboard.findall(".//zone")
        zone_count = len(zones)

        return {
            "index": index,
            "name": name,
            "sort_zone_enabled": sort_zone_enabled,
            "zone_count": zone_count,
        }

    def print_dashboards(self, dashboards: List[Dict[str, Any]]) -> None:
        """Print dashboards in a formatted way to console.

        Args:
            dashboards: List of dashboard dictionaries
        """
        if not dashboards:
            print("No dashboards found.")
            return

        print(f"\n{len(dashboards)} Dashboard(s)")
        print()
        print("DASHBOARD NAME")
        print("-" * 50)

        for dashboard in dashboards:
            print(f"{dashboard['index']:<3} {dashboard['name']}")

    def run(self) -> List[Dict[str, Any]]:
        """Run the dashboard extraction process.

        Returns:
            List of dashboard dictionaries
        """
        dashboards = self.extract_dashboards()
        self.print_dashboards(dashboards=dashboards)
        return dashboards


def extract_dashboards_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Utility function to extract dashboards from a Tableau workbook file.

    Args:
        file_path: Path to the Tableau workbook file

    Returns:
        List of dashboard dictionaries
    """
    extractor = DashboardExtractor(file_path=file_path)
    return extractor.run()
