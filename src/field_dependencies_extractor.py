"""
Tableau field dependencies analyzer - maps field usage relationships.
Shows which fields are used by other calculated fields and where they appear.
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Set, Any
from pathlib import Path
import logging


class FieldDependenciesAnalyzer:
    """Analyzes field dependencies in Tableau workbooks."""

    def __init__(self, file_path: str) -> None:
        """Initialize the analyzer.

        Args:
            file_path: Path to the Tableau workbook file (.twb)
        """
        self.file_path = Path(file_path)
        self.logger = logging.getLogger(__name__)

    def analyze_field_dependencies(self) -> List[Dict[str, Any]]:
        """Analyze field dependencies in the workbook.

        Returns:
            List of field dependency dictionaries
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Tableau file not found: {self.file_path}")

        try:
            tree = ET.parse(self.file_path)
            root = tree.getroot()

            # Get all field definitions
            field_definitions = self._extract_field_definitions(root=root)

            # Analyze dependencies
            dependencies = self._extract_field_dependencies(
                root=root, field_definitions=field_definitions
            )

            # Create results
            results = self._create_dependency_results(dependencies=dependencies)

            return results

        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def _extract_field_definitions(self, root: ET.Element) -> Dict[str, str]:
        """Extract field definitions with display names.

        Args:
            root: Root XML element

        Returns:
            Dictionary mapping field keys to display names
        """
        field_definitions = {}

        # Extract from datasource column definitions
        for datasource in root.findall(".//datasource"):
            for column in datasource.findall(".//column"):
                field_name = column.get("name", "")
                if not field_name or not field_name.startswith("["):
                    continue

                caption = column.get("caption", "")
                display_name = caption if caption else field_name[1:-1]
                field_definitions[field_name] = display_name

        # Also check datasource-dependencies for additional fields
        for datasource_deps in root.findall(".//datasource-dependencies"):
            for column in datasource_deps.findall(".//column"):
                field_name = column.get("name", "")
                if not field_name or not field_name.startswith("["):
                    continue

                if field_name not in field_definitions:
                    caption = column.get("caption", "")
                    display_name = caption if caption else field_name[1:-1]
                    field_definitions[field_name] = display_name

        return field_definitions

    def _extract_field_dependencies(
        self, root: ET.Element, field_definitions: Dict[str, str]
    ) -> Dict[str, Set[str]]:
        """Extract field dependencies from calculations.

        Args:
            root: Root XML element
            field_definitions: Field definitions

        Returns:
            Dictionary mapping field names to sets of dependent fields
        """
        dependencies = {}

        # Analyze calculated field formulas
        for column in root.findall(".//column"):
            calculation = column.find(".//calculation")
            if calculation is not None:
                field_name = column.get("name", "")
                caption = column.get("caption", "")

                if field_name and field_name.startswith("["):
                    # Get the display name for this calculated field
                    calc_display_name = caption if caption else field_name[1:-1]

                    formula = calculation.get("formula", "")
                    if formula:
                        # Find field references in the formula
                        referenced_fields = self._extract_field_references_from_formula(
                            formula=formula, field_definitions=field_definitions
                        )

                        # Add this calculated field as a dependent for each referenced field
                        for ref_field in referenced_fields:
                            if ref_field not in dependencies:
                                dependencies[ref_field] = set()
                            dependencies[ref_field].add(calc_display_name)

        # Also check parameter usage in formulas by finding columns with calculations
        for column in root.findall(".//column"):
            calculation = column.find(".//calculation")
            if calculation is not None:
                formula = calculation.get("formula", "")
                if formula and "[Parameters]." in formula:
                    calc_field_name = column.get("name", "")
                    calc_caption = column.get("caption", "")
                    calc_display_name = (
                        calc_caption
                        if calc_caption
                        else (
                            calc_field_name[1:-1]
                            if calc_field_name.startswith("[")
                            else calc_field_name
                        )
                    )

                    # Extract parameter references
                    param_refs = re.findall(r"\[Parameters\]\.\[([^\]]+)\]", formula)
                    for param_name in param_refs:
                        param_display_name = param_name
                        if param_display_name not in dependencies:
                            dependencies[param_display_name] = set()
                        dependencies[param_display_name].add(calc_display_name)

        return dependencies

    def _extract_field_references_from_formula(
        self, formula: str, field_definitions: Dict[str, str]
    ) -> Set[str]:
        """Extract field references from a calculation formula.

        Args:
            formula: Calculation formula
            field_definitions: Field definitions

        Returns:
            Set of referenced field display names
        """
        referenced_fields = set()

        # Find field patterns like [Field Name] in the formula
        field_pattern = r"\[([^\]]+)\]"
        matches = re.findall(field_pattern, formula)

        for match in matches:
            # Skip function names and special cases
            if match.upper() in [
                "SUM",
                "AVG",
                "COUNT",
                "MIN",
                "MAX",
                "IF",
                "THEN",
                "ELSE",
                "END",
            ]:
                continue
            if "(" in match or ")" in match:
                continue
            if match.startswith("Parameters"):
                continue

            # Try to find the display name for this field reference
            field_key = f"[{match}]"
            if field_key in field_definitions:
                referenced_fields.add(field_definitions[field_key])
            else:
                # If not found in definitions, use the raw field name
                referenced_fields.add(match)

        return referenced_fields

    def _create_dependency_results(
        self, dependencies: Dict[str, Set[str]]
    ) -> List[Dict[str, Any]]:
        """Create formatted dependency results.

        Args:
            dependencies: Field dependencies

        Returns:
            List of dependency dictionaries
        """
        results = []

        for field_name, dependent_fields in dependencies.items():
            if dependent_fields:  # Only include fields that have dependencies
                where_used = " | ".join(sorted(dependent_fields))
                used_times = len(dependent_fields)

                results.append(
                    {
                        "field_name": field_name,
                        "where_used": where_used,
                        "used_times": used_times,
                    }
                )

        # Sort by usage count (descending) then by field name
        results.sort(key=lambda x: (-x["used_times"], x["field_name"]))

        return results

    def print_results(self, results: List[Dict[str, Any]]) -> None:
        """Print results in reference format.

        Args:
            results: List of dependency dictionaries
        """
        if not results:
            print("No field dependencies found.")
            return

        print('\nFIELD DEPENDENCIES TABLE (Fields separated by "|")')
        print("=" * 80)
        print()
        print(f"{'FIELD NAME':<25} {'WHERE IS IT USED':<40} {'USED_TIMES'}")
        print("-" * 80)

        for i, field in enumerate(results, 1):
            name = field["field_name"][:24]
            where_used = field["where_used"][:39]
            used_times = str(field["used_times"])
            print(f"{i:<3} {name:<22} {where_used:<37} {used_times}")

        print(f"\nShowing 1 to {len(results)} of {len(results)} entries")

    def run(self) -> List[Dict[str, Any]]:
        """Run the analysis.

        Returns:
            List of dependency dictionaries
        """
        results = self.analyze_field_dependencies()
        self.print_results(results=results)
        return results


def extract_field_dependencies(file_path: str) -> List[Dict[str, Any]]:
    """Extract field dependencies from Tableau workbook file.

    Args:
        file_path: Path to Tableau workbook file

    Returns:
        List of dependency dictionaries
    """
    analyzer = FieldDependenciesAnalyzer(file_path=file_path)
    return analyzer.run()
