"""
Tableau fields analyzer - precisely matches the reference field usage analysis.
Focuses on actual field usage in visualizations and worksheet contexts.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Set
from pathlib import Path
import logging


class TableauFieldsAnalyzer:
    """Analyzes field usage in Tableau workbooks matching reference methodology."""

    def __init__(self, file_path: str) -> None:
        """Initialize the analyzer.

        Args:
            file_path: Path to the Tableau workbook file (.twb)
        """
        self.file_path = Path(file_path)
        self.logger = logging.getLogger(__name__)

    def analyze_fields_usage(self) -> List[Dict[str, Any]]:
        """Analyze field usage matching the reference format.

        Returns:
            List of field usage dictionaries
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Tableau file not found: {self.file_path}")

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            # Get field definitions with types
            field_definitions = self._extract_field_definitions(root=root)

            # Count field usage in worksheets
            field_usage_counts = self._count_worksheet_field_usage(root=root)

            # Create final results
            results = self._create_usage_results(
                field_definitions=field_definitions, usage_counts=field_usage_counts
            )

            return results

        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def _extract_field_definitions(self, root: ET.Element) -> Dict[str, Dict[str, str]]:
        """Extract field definitions with their types.

        Args:
            root: Root XML element

        Returns:
            Dictionary mapping field keys to their properties
        """
        field_definitions = {}

        # Extract from datasource column definitions
        for datasource in root.findall(".//datasource"):
            datasource_name = datasource.get("name", "")

            # Skip Parameters datasource for field definitions
            if datasource_name == "Parameters":
                continue

            for column in datasource.findall(".//column"):
                field_name = column.get("name", "")
                if not field_name or not field_name.startswith("["):
                    continue

                caption = column.get("caption", "")
                display_name = caption if caption else field_name[1:-1]

                field_type = self._determine_field_type(column=column)

                field_definitions[field_name] = {
                    "display_name": display_name,
                    "field_type": field_type,
                }

        # Also check datasource-dependencies for additional fields
        for datasource_deps in root.findall(".//datasource-dependencies"):
            for column in datasource_deps.findall(".//column"):
                field_name = column.get("name", "")
                if not field_name or not field_name.startswith("["):
                    continue

                if field_name not in field_definitions:
                    caption = column.get("caption", "")
                    display_name = caption if caption else field_name[1:-1]
                    field_type = self._determine_field_type(column=column)

                    field_definitions[field_name] = {
                        "display_name": display_name,
                        "field_type": field_type,
                    }

        return field_definitions

    def _determine_field_type(self, column: ET.Element) -> str:
        """Determine field type from column element.

        Args:
            column: Column XML element

        Returns:
            Field type string
        """
        # Check for parameter
        if column.get("param-domain-type") is not None:
            return "Parameter"

        # Check for calculated field
        calculation = column.find(".//calculation")
        if calculation is not None:
            return "Calculated Field"

        return "Raw Variable"

    def _count_worksheet_field_usage(self, root: ET.Element) -> Dict[str, int]:
        """Count field usage based on worksheet contexts.

        Args:
            root: Root XML element

        Returns:
            Dictionary mapping field names to usage counts
        """
        usage_counts = {}

        # Analyze each worksheet individually
        for worksheet in root.findall(".//worksheet"):
            worksheet_name = worksheet.get("name", "")
            worksheet_fields = self._get_worksheet_fields(worksheet=worksheet)

            # Count each unique field once per worksheet
            for field_name in worksheet_fields:
                usage_counts[field_name] = usage_counts.get(field_name, 0) + 1

        # Analyze dashboards
        for dashboard in root.findall(".//dashboard"):
            dashboard_name = dashboard.get("name", "")
            dashboard_fields = self._get_dashboard_fields(dashboard=dashboard)

            # Count each unique field once per dashboard
            for field_name in dashboard_fields:
                usage_counts[field_name] = usage_counts.get(field_name, 0) + 1

        return usage_counts

    def _get_worksheet_fields(self, worksheet: ET.Element) -> Set[str]:
        """Get all fields used in a worksheet context.

        Args:
            worksheet: Worksheet XML element

        Returns:
            Set of field names used in this worksheet
        """
        worksheet_fields = set()

        # Get fields from datasource-dependencies within this worksheet
        # This captures all fields that are available/referenced in this context
        for datasource_deps in worksheet.findall(".//datasource-dependencies"):
            datasource_name = datasource_deps.get("datasource", "")

            # Skip Parameters datasource
            if datasource_name == "Parameters":
                continue

            for column_instance in datasource_deps.findall(".//column-instance"):
                field_name = column_instance.get("column", "")
                if field_name and field_name.startswith("["):
                    clean_name = self._clean_field_name(field_name=field_name)
                    if clean_name:
                        worksheet_fields.add(clean_name)

        # Also check visual encodings for direct usage
        for encoding in worksheet.findall(".//encoding[@attr]"):
            field_name = encoding.get("field", "")
            if field_name and field_name.startswith("["):
                clean_name = self._clean_field_name(field_name=field_name)
                if clean_name:
                    worksheet_fields.add(clean_name)

        # Check shelves (rows/columns)
        for pane in worksheet.findall(".//panes/pane"):
            for view_col in pane.findall(".//view/cols/column"):
                field_name = view_col.text or ""
                if field_name and field_name.startswith("["):
                    clean_name = self._clean_field_name(field_name=field_name)
                    if clean_name:
                        worksheet_fields.add(clean_name)

            for view_row in pane.findall(".//view/rows/column"):
                field_name = view_row.text or ""
                if field_name and field_name.startswith("["):
                    clean_name = self._clean_field_name(field_name=field_name)
                    if clean_name:
                        worksheet_fields.add(clean_name)

        return worksheet_fields

    def _get_dashboard_fields(self, dashboard: ET.Element) -> Set[str]:
        """Get all fields used in a dashboard.

        Args:
            dashboard: Dashboard XML element

        Returns:
            Set of field names used in this dashboard
        """
        dashboard_fields = set()

        # Check encodings in dashboards
        for encoding in dashboard.findall(".//encoding[@attr]"):
            field_name = encoding.get("field", "")
            if field_name and field_name.startswith("["):
                clean_name = self._clean_field_name(field_name=field_name)
                if clean_name:
                    dashboard_fields.add(clean_name)

        return dashboard_fields

    def _clean_field_name(self, field_name: str) -> str:
        """Clean field name by removing derivation prefixes.

        Args:
            field_name: Original field name

        Returns:
            Clean field name
        """
        if not field_name or not field_name.startswith("["):
            return field_name

        # Remove outer brackets
        inner = field_name[1:-1]

        # Handle derivation patterns like 'mn:Order Date:ok'
        if ":" in inner:
            parts = inner.split(":")
            if len(parts) >= 2:
                field_part = parts[1]
                return f"[{field_part}]"

        return field_name

    def _extract_field_from_filter(self, filter_column: str) -> str:
        """Extract field name from filter column reference.

        Args:
            filter_column: Filter column string

        Returns:
            Clean field name or empty string
        """
        if not filter_column or "].[" not in filter_column:
            return ""

        field_part = filter_column.split("].")[-1]
        if field_part.startswith("[") and field_part.endswith("]:"):
            field_name = field_part[:-1]  # Remove trailing colon
            return self._clean_field_name(field_name=field_name)

        return ""

    def _create_usage_results(
        self, field_definitions: Dict[str, Dict[str, str]], usage_counts: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Create final usage results.

        Args:
            field_definitions: Field definitions
            usage_counts: Usage counts

        Returns:
            List of field usage dictionaries
        """
        results = []

        for field_key, field_info in field_definitions.items():
            usage_count = usage_counts.get(field_key, 0)

            if usage_count > 0:  # Only include used fields
                results.append(
                    {
                        "field_name": field_info["display_name"],
                        "field_type": field_info["field_type"],
                        "used_times": usage_count,
                    }
                )

        # Sort by usage count (descending) then by name
        results.sort(key=lambda x: (-x["used_times"], x["field_name"]))

        return results

    def print_results(self, results: List[Dict[str, Any]]) -> None:
        """Print results in reference format.

        Args:
            results: List of field usage dictionaries
        """
        if not results:
            print("No fields found.")
            return

        print("\nFIELDS USED")
        print("=" * 80)
        print()
        print(f"{'FIELD NAME':<30} {'FIELD TYPE':<20} {'USED_TIMES'}")
        print("-" * 70)

        for i, field in enumerate(results, 1):
            name = field["field_name"][:29]
            field_type = field["field_type"][:19]
            usage = str(field["used_times"])
            print(f"{i:<3} {name:<27} {field_type:<19} {usage}")

        print(f"\nShowing 1 to {len(results)} of {len(results)} entries")

    def run(self) -> List[Dict[str, Any]]:
        """Run the analysis.

        Returns:
            List of field usage dictionaries
        """
        results = self.analyze_fields_usage()
        self.print_results(results=results)
        return results


def analyze_tableau_fields(file_path: str) -> List[Dict[str, Any]]:
    """Analyze Tableau fields usage from workbook file.

    Args:
        file_path: Path to Tableau workbook file

    Returns:
        List of field usage dictionaries
    """
    analyzer = TableauFieldsAnalyzer(file_path=file_path)
    return analyzer.run()
