"""Configuration settings for Flavour Graph project."""
from pathlib import Path
import os

# Project root directory
# Works both in development and when installed as package
if os.path.exists(Path(__file__).parent.parent / "data"):
    # Development mode - running from repository
    PROJECT_ROOT = Path(__file__).parent.parent
else:
    # Installed mode - use current working directory
    PROJECT_ROOT = Path.cwd()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Output subdirectories
INTERACTIVE_OUTPUT = OUTPUT_DIR / "interactive"
EMBEDDINGS_OUTPUT = OUTPUT_DIR / "embeddings"
VISUALIZATIONS_OUTPUT = OUTPUT_DIR / "visualizations"

# Data files
PRODUCTS_FILE = DATA_DIR / "products.json"
PRODUCTS_PARQUET = DATA_DIR / "products.parquet"
RELATIONS_FILE = DATA_DIR / "product_relations.json"
SUBCATEGORIES_FILE = DATA_DIR / "Subcategories.xlsx"
SALES_FILE = DATA_DIR / "Sales_2025.parquet"

# Model files
EMBEDDINGS_MODEL = DATA_DIR / "embeddings_model.pkl"
EMBEDDINGS_WORD2VEC = DATA_DIR / "embeddings_model_word2vec.model"

# Default parameters
DEFAULT_MIN_EDGE_WEIGHT = 5.0
DEFAULT_EMBEDDING_DIMENSIONS = 64

# Visualization settings
DEFAULT_FIGSIZE = (20, 20)
DEFAULT_DPI = 150

# Create directories if they don't exist
for directory in [OUTPUT_DIR, INTERACTIVE_OUTPUT, EMBEDDINGS_OUTPUT, VISUALIZATIONS_OUTPUT]:
    directory.mkdir(parents=True, exist_ok=True)
