"""
Tableau field dependencies network visualizer.
Creates network graphs showing field relationships and dependencies.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple
from pathlib import Path
import logging

try:
    import networkx as nx
    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    nx = None
    matplotlib = None
    plt = None
    mpatches = None

from field_dependencies_extractor import FieldDependenciesAnalyzer


class FieldDependenciesNetworkVisualizer:
    """Creates network visualizations of field dependencies in Tableau workbooks."""

    def __init__(self, file_path: str, output_dir: str = "output") -> None:
        """Initialize the network visualizer.

        Args:
            file_path: Path to the Tableau workbook file (.twb)
            output_dir: Directory to save output plots
        """
        self.file_path = Path(file_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        if not VISUALIZATION_AVAILABLE:
            raise ImportError(
                "Required packages not available. "
                "Please install: pip install networkx matplotlib"
            )

    def create_dependencies_network(self) -> nx.DiGraph:
        """Create a network graph of field dependencies.

        Returns:
            NetworkX directed graph of field dependencies
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Tableau file not found: {self.file_path}")

        # Use the existing FieldDependenciesAnalyzer to get dependencies
        analyzer = FieldDependenciesAnalyzer(file_path=str(self.file_path))
        dependencies_results = analyzer.analyze_field_dependencies()

        # Also get field definitions and types
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        field_types = self._extract_field_types(root=root)

        # Create directed graph
        graph = nx.DiGraph()

        # Add nodes and edges based on dependencies
        for dependency in dependencies_results:
            source_field = dependency["field_name"]
            used_times = dependency["used_times"]
            dependent_fields = dependency["where_used"].split(" | ")

            # Add source node with attributes
            field_type = field_types.get(source_field, "Unknown")
            graph.add_node(
                source_field,
                field_type=field_type,
                used_times=used_times,
                node_type="source",
            )

            # Add dependent nodes and edges
            for dependent_field in dependent_fields:
                dependent_field = dependent_field.strip()
                if dependent_field:
                    dependent_type = field_types.get(
                        dependent_field, "Calculated Field"
                    )
                    graph.add_node(
                        dependent_field,
                        field_type=dependent_type,
                        used_times=0,  # Dependent fields don't have usage counts
                        node_type="dependent",
                    )

                    # Add edge from source to dependent
                    graph.add_edge(source_field, dependent_field)

        return graph

    def _extract_field_types(self, root: ET.Element) -> Dict[str, str]:
        """Extract field types for all fields.

        Args:
            root: Root XML element

        Returns:
            Dictionary mapping field names to their types
        """
        field_types = {}

        # Extract from datasource column definitions
        for datasource in root.findall(".//datasource"):
            datasource_name = datasource.get("name", "")

            for column in datasource.findall(".//column"):
                field_name = column.get("name", "")
                caption = column.get("caption", "")
                display_name = (
                    caption
                    if caption
                    else field_name[1:-1] if field_name.startswith("[") else field_name
                )

                if display_name:
                    # Determine field type
                    if datasource_name == "Parameters":
                        field_types[display_name] = "Parameter"
                    elif column.find(".//calculation") is not None:
                        field_types[display_name] = "Calculated Field"
                    else:
                        field_types[display_name] = "Raw Variable"

        # Also check datasource-dependencies for additional fields
        for datasource_deps in root.findall(".//datasource-dependencies"):
            for column in datasource_deps.findall(".//column"):
                field_name = column.get("name", "")
                caption = column.get("caption", "")
                display_name = (
                    caption
                    if caption
                    else field_name[1:-1] if field_name.startswith("[") else field_name
                )

                if display_name and display_name not in field_types:
                    if column.get("param-domain-type") is not None:
                        field_types[display_name] = "Parameter"
                    elif column.find(".//calculation") is not None:
                        field_types[display_name] = "Calculated Field"
                    else:
                        field_types[display_name] = "Raw Variable"

        return field_types

    def _get_node_colors_and_sizes(
        self, graph: nx.DiGraph
    ) -> Tuple[List[str], List[float]]:
        """Get node colors and sizes based on field types and usage.

        Args:
            graph: NetworkX graph

        Returns:
            Tuple of (colors, sizes) lists
        """
        colors = []
        sizes = []

        # Color mapping for field types
        color_map = {
            "Raw Variable": "#87CEEB",  # Light blue
            "Calculated Field": "#FFB6C1",  # Light pink
            "Parameter": "#98FB98",  # Light green
            "Unknown": "#D3D3D3",  # Light gray
        }

        for node in graph.nodes():
            node_data = graph.nodes[node]
            field_type = node_data.get("field_type", "Unknown")
            used_times = node_data.get("used_times", 0)

            # Set color based on field type
            colors.append(color_map.get(field_type, color_map["Unknown"]))

            # Set size based on usage (source nodes) or default for dependent nodes
            if used_times > 0:
                # Scale size based on usage: min 300, max 2000
                size = max(300, min(2000, 300 + (used_times * 200)))
            else:
                # Default size for dependent nodes
                size = 500

            sizes.append(size)

        return colors, sizes

    def visualize_network(
        self,
        graph: nx.DiGraph,
        title: str = "Field Dependencies Network",
        save_filename: str = "field_dependencies_network.png",
    ) -> None:
        """Create and save network visualization.

        Args:
            graph: NetworkX graph to visualize
            title: Title for the plot
            save_filename: Filename to save the plot
        """
        if not graph.nodes():
            self.logger.warning("No nodes in graph to visualize")
            return

        # Set up the plot
        plt.figure(figsize=(16, 12))
        plt.title(title, fontsize=16, fontweight="bold", pad=20)

        # Get node colors and sizes
        colors, sizes = self._get_node_colors_and_sizes(graph=graph)

        # Create layout using spring layout for better visualization
        try:
            pos = nx.spring_layout(
                graph,
                k=3,  # Optimal distance between nodes
                iterations=50,  # Number of iterations
                seed=42,  # For reproducible layouts
            )
        except:
            # Fallback to circular layout if spring layout fails
            pos = nx.circular_layout(graph)

        # Draw edges first (so they appear behind nodes)
        nx.draw_networkx_edges(
            graph,
            pos,
            edge_color="lightgray",
            arrows=True,
            arrowsize=20,
            arrowstyle="->",
            alpha=0.6,
            width=1.5,
        )

        # Draw nodes
        nx.draw_networkx_nodes(
            graph,
            pos,
            node_color=colors,
            node_size=sizes,
            alpha=0.8,
            edgecolors="black",
            linewidths=1,
        )

        # Draw labels
        nx.draw_networkx_labels(
            graph, pos, font_size=8, font_weight="bold", font_color="black"
        )

        # Create legend
        legend_elements = [
            mpatches.Patch(color="#87CEEB", label="Raw Variable"),
            mpatches.Patch(color="#FFB6C1", label="Calculated Field"),
            mpatches.Patch(color="#98FB98", label="Parameter"),
            mpatches.Patch(color="#D3D3D3", label="Unknown"),
        ]

        plt.legend(
            handles=legend_elements,
            loc="upper left",
            bbox_to_anchor=(0, 1),
            frameon=True,
            fancybox=True,
            shadow=True,
        )

        # Add note about node sizes
        plt.figtext(
            0.02,
            0.02,
            "Note: Node size represents how many times the field is used by other fields",
            fontsize=10,
            style="italic",
        )

        # Remove axis
        plt.axis("off")

        # Adjust layout to prevent clipping
        plt.tight_layout()

        # Save the plot
        output_path = self.output_dir / save_filename
        plt.savefig(
            output_path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )

        self.logger.info(f"Network visualization saved to: {output_path}")

        # Close the plot to free memory (don't show in headless environment)
        plt.close()

    def generate_network_statistics(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """Generate statistics about the network.

        Args:
            graph: NetworkX graph

        Returns:
            Dictionary of network statistics
        """
        stats = {
            "total_nodes": graph.number_of_nodes(),
            "total_edges": graph.number_of_edges(),
            "density": nx.density(graph),
            "is_connected": nx.is_weakly_connected(graph),
        }

        # Node type distribution
        field_types = {}
        for node in graph.nodes():
            field_type = graph.nodes[node].get("field_type", "Unknown")
            field_types[field_type] = field_types.get(field_type, 0) + 1

        stats["field_type_distribution"] = field_types

        # Most connected nodes
        in_degrees = dict(graph.in_degree())
        out_degrees = dict(graph.out_degree())

        if in_degrees:
            most_dependent = max(in_degrees.items(), key=lambda x: x[1])
            stats["most_dependent_field"] = most_dependent

        if out_degrees:
            most_used = max(out_degrees.items(), key=lambda x: x[1])
            stats["most_used_field"] = most_used

        return stats

    def print_network_statistics(self, stats: Dict[str, Any]) -> None:
        """Print network statistics in a formatted way.

        Args:
            stats: Network statistics dictionary
        """
        print("\nFIELD DEPENDENCIES NETWORK STATISTICS")
        print("=" * 50)
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Total Edges: {stats['total_edges']}")
        print(f"Network Density: {stats['density']:.3f}")
        print(f"Is Connected: {stats['is_connected']}")

        if "field_type_distribution" in stats:
            print("\nField Type Distribution:")
            for field_type, count in stats["field_type_distribution"].items():
                print(f"  {field_type}: {count}")

        if "most_used_field" in stats:
            field_name, usage_count = stats["most_used_field"]
            print(f"\nMost Used Field: {field_name} (used by {usage_count} fields)")

        if "most_dependent_field" in stats:
            field_name, dependency_count = stats["most_dependent_field"]
            print(
                f"Most Dependent Field: {field_name} (depends on {dependency_count} fields)"
            )

    def run(self, save_filename: str = "field_dependencies_network.png") -> nx.DiGraph:
        """Run the complete network analysis and visualization.

        Args:
            save_filename: Filename to save the network plot

        Returns:
            NetworkX graph of field dependencies
        """
        # Create the network
        graph = self.create_dependencies_network()

        # Generate and print statistics
        stats = self.generate_network_statistics(graph=graph)
        self.print_network_statistics(stats=stats)

        # Create visualization
        self.visualize_network(graph=graph, save_filename=save_filename)

        return graph


def create_field_dependencies_network(
    file_path: str,
    output_dir: str = "output",
    save_filename: str = "field_dependencies_network.png",
) -> nx.DiGraph:
    """Create field dependencies network visualization from Tableau workbook file.

    Args:
        file_path: Path to Tableau workbook file
        output_dir: Directory to save output plots
        save_filename: Filename to save the network plot

    Returns:
        NetworkX graph of field dependencies
    """
    visualizer = FieldDependenciesNetworkVisualizer(
        file_path=file_path, output_dir=output_dir
    )
    return visualizer.run(save_filename=save_filename)
