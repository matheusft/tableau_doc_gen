# Tableau Documentation Generator

A Python tool for extracting comprehensive information from Tableau workbook files (.twb) and generating detailed documentation.

## Overview

This tool analyzes Tableau workbook XML files to extract and document various components including data sources, worksheets, dashboards, field dependencies, and usage patterns.

## Features

### Data Sources & Tables
- Extract data source metadata (names, connection types, configuration)
- Identify table structures and relationships
- Map connection information

### Field Analysis
- Complete field inventory with data types and roles
- Usage analysis (used vs unused fields)
- Field dependency mapping
- Calculated field formulas and dependency chains

### Worksheets & Dashboards
- Extract worksheet configurations
- Map dashboard layouts and components
- Document visualization settings

### Network Visualization
- Generate visual graph of field dependencies
- Show relationships between calculated and source fields
- Export as PNG image

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tableau_doc_gen
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Configure via `config/config.yaml`:

```yaml
tableau:
  file_path: "tableau_file/Superstore.twb"
  
datasource:
  enabled: true
  output_format: "console"
  
table:
  enabled: true
  output_format: "console"
  extract_worksheets: true
  extract_dashboards: true
  
output:
  directory: "output"
  
logging:
  level: "INFO"
```

## Usage

```bash
python src/main.py
```

The tool will:
1. Parse the Tableau workbook
2. Extract data sources, tables, worksheets, and dashboards
3. Analyze field usage and dependencies
4. Generate network visualization
5. Output results to console and `output/` directory

## Output

- **Console**: Summary statistics and tables
- **Network Graph**: `output/field_dependencies_network.png`

## Project Structure

```
tableau_doc_gen/
├── config/
│   ├── config.yaml
│   └── config_manager.py
├── src/
│   ├── main.py
│   ├── datasource_extractor.py
│   ├── table_extractor.py
│   ├── worksheet_extractor.py
│   ├── dashboard_extractor.py
│   ├── tableau_fields_analyzer.py
│   ├── field_dependencies_extractor.py
│   └── field_dependencies_network.py
├── tableau_file/
│   └── Superstore.twb
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8+
- munch==4.0.0
- PyYAML==6.0.2
- networkx==3.5
- matplotlib==3.10.6
