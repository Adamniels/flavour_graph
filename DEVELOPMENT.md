# Development Guide

## Installation för utveckling

### 1. Klona repository
```bash
git clone https://github.com/Adamniels/flavour_graph.git
cd flavour_graph
```

### 2. Skapa virtual environment
```bash
python -m venv venv
source venv/bin/activate  # På macOS/Linux
# eller
venv\Scripts\activate  # På Windows
```

### 3. Installera i development mode
```bash
# Installera paketet i editable mode med dev dependencies
pip install -e ".[dev]"

# Eller installera bara dependencies
pip install -r requirements.txt
```

## Projektstruktur

```
flavour_graph/
├── src/                    # Källkod (Python package)
│   ├── __init__.py
│   ├── config.py          # Konfiguration och paths
│   ├── core/              # Kärnfunktionalitet
│   ├── embeddings/        # Node2Vec embeddings
│   ├── interactive/       # HTML visualiseringar
│   └── visualization/     # Matplotlib visualiseringar
│
├── scripts/               # Utility scripts
├── data/                  # Data-filer (not in git)
├── output/                # Genererade filer (not in git)
│
├── run_*.py              # Entry point scripts
├── setup.py              # Package setup
├── pyproject.toml        # Modern Python packaging
├── requirements.txt      # Dependencies
└── README.md             # User documentation
```

## Användning

### Som scripts (development mode)
```bash
# Direkt från repository
python run_interactive.py
python run_embeddings.py --visualize
python run_visualization.py
```

### Som installerat package
```bash
# Efter `pip install -e .`
flavour-interactive
flavour-embeddings --visualize
flavour-visualize
```

### Som Python module
```python
from src.core import setup_graph, generate
from src.embeddings import ProductEmbeddings
from src.interactive import generate_html_visualization

# Använd funktionerna
G = setup_graph()
embeddings = ProductEmbeddings(G)
```

## Kodstandard

### Formatering med Black
```bash
black src/ scripts/ *.py
```

### Linting med Flake8
```bash
flake8 src/ scripts/
```

### Type checking med MyPy
```bash
mypy src/
```

## Testing

### Kör alla tester
```bash
pytest
```

### Kör specifikt test
```bash
pytest tests/test_embeddings.py
```

### Med coverage
```bash
pytest --cov=src --cov-report=html
```

## Git Workflow

### Branches
- `main` - Stable release branch
- `develop` - Development branch
- `feature/*` - Feature branches
- `fix/*` - Bug fix branches

### Commit messages
```
feat: Add new visualization type
fix: Correct import path in embeddings
docs: Update README with installation instructions
refactor: Reorganize project structure
test: Add tests for similarity search
```

## Package Distribution

### Build package
```bash
python -m build
```

### Upload to PyPI (för framtiden)
```bash
twine upload dist/*
```

## Common Tasks

### Regenerera alla visualiseringar
```bash
python run_interactive.py
python run_embeddings.py --visualize --visualize-3d --visualize-weights
python run_visualization.py
```

### Konvertera sales data
```bash
python scripts/convert_sales_to_user_pattern.py
```

### Testa connections
```bash
python scripts/test_connections.py
```

## Troubleshooting

### Import errors
Om du får import errors, säkerställ att du kör från project root:
```bash
cd /path/to/flavour_graph
python run_interactive.py
```

Eller installera paketet:
```bash
pip install -e .
```

### Missing data files
Kontrollera att du har:
- `data/products.json`
- `data/product_relations.json`
- `data/Subcategories.xlsx`

### Memory issues
För stora grafer, öka minne eller minska dataset:
```python
G = setup_graph(min_edge_weight=10.0)  # Higher threshold = fewer edges
```

## Contributing

1. Fork repository
2. Skapa feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Öppna Pull Request

## Support

- 📧 Email: [your-email]
- 🐛 Issues: https://github.com/Adamniels/flavour_graph/issues
- 📖 Wiki: https://github.com/Adamniels/flavour_graph/wiki
