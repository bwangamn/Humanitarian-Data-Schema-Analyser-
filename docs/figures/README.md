# System Architecture & Diagram Assets

This directory contains system architecture diagrams, data flow diagrams (DFD), and component interaction diagrams for the **Humanitarian Data Schema Analyser**.

## System Architecture Diagram
```mermaid
graph TD
    A[Input Humanitarian Datasets: CSV, JSON, XML, XLSForm, HXL, IATI] --> B[CLI Interface / Typer Controller]
    B --> C[Parser Factory]
    C --> D1[CSV Parser]
    C --> D2[JSON Parser]
    C --> D3[XML / XForms / IATI Parser]
    C --> D4[XLSForm Parser]
    D1 --> E[Raw Metadata & Dataframe Extraction]
    D2 --> E
    D3 --> E
    D4 --> E
    E --> F[Profiling Engine / Statistical Profiler]
    F --> G[Unified Schema Model Dataclass]
    G --> H1[Schema Builder: JSON Schema Draft 2020-12 Generator]
    G --> H2[HTML Report Generator]
    H1 --> I1[JSON Schema Document]
    H2 --> I2[Interactive HTML Summary Report]
```

## Data Flow Diagram (DFD)
```mermaid
sequenceDiagram
    autonumber
    actor User as Technical User / CLI
    participant Factory as ParserFactory
    participant Parser as Format Parser (CSV/JSON/XML/XLS)
    participant Profiler as Profiling Engine
    participant Model as Unified Schema Model
    participant Generator as Output Generators (JSON/HTML)

    User->>Factory: Invoke profile command (file_path, options)
    Factory->>Parser: Select and instantiate parser
    Parser->>Parser: Extract fields, types, raw records & HXL tags
    Parser-->>Profiler: Pass extracted tabular data
    Parser-->>Profiler: Pass extracted tabular data
    Profiler->>Profiler: Compute missing counts, unique values, min/max/mean/std, date formats
    Profiler->>Model: Construct UnifiedSchema & ColumnProfile objects
    Model-->>Generator: Pass UnifiedSchema instance
    Generator->>Generator: Build JSON Schema (jsonschema) & HTML Report (Jinja2/Bootstrap)
    Generator-->>User: Return JSON Schema & HTML report outputs
```

## Component Diagram
```mermaid
graph LR
    subgraph CLI Component
        CLI[cli/main.py]
    end
    subgraph Parser Component
        Factory[parsers/factory.py]
        Base[parsers/base_parser.py]
        CSV[parsers/csv_parser.py]
        JSON[parsers/json_parser.py]
        XML[parsers/xml_parser.py]
        XLS[parsers/xls_parser.py]
    end
    subgraph Profiling Component
        Prof[profiling/profiler.py]
    end
    subgraph Schema Representation
        Model[schema/unified_model.py]
        Builder[schema/schema_builder.py]
    end
    subgraph Report Component
        HTML[reports/html_report.py]
    end

    CLI --> Factory
    Factory --> Base
    Base <|-- CSV
    Base <|-- JSON
    Base <|-- XML
    Base <|-- XLS
    CLI --> Prof
    Prof --> Model
    CLI --> Builder
    Builder --> Model
    CLI --> HTML
    HTML --> Model
```
