# Troubleshooting Guide

## Pylance Import Errors

### Problem: "Import 'setuptools' could not be resolved"

**Orsak:** Pylance kan inte hitta setuptools i din virtual environment.

**Lösning:**
```bash
# Aktivera virtual environment
source venv/bin/activate  # macOS/Linux
# eller
venv\Scripts\activate  # Windows

# Installera setuptools och build tools
pip install setuptools wheel build

# Installera paketet i editable mode
pip install -e .
```

### Problem: "Import 'src.module' could not be resolved"

**Orsak:** Paketet är inte installerat i virtual environment.

**Lösning:**
```bash
# Från project root
pip install -e .
```

### Problem: Pylance använder fel Python interpreter

**Lösning i VS Code:**
1. Tryck `Cmd+Shift+P` (eller `Ctrl+Shift+P` på Windows)
2. Välj "Python: Select Interpreter"
3. Välj din venv: `./venv/bin/python`

## Import Errors vid körning

### Problem: "ModuleNotFoundError: No module named 'src'"

**Orsak:** Du kör inte från project root eller paketet är inte installerat.

**Lösning 1 - Kör från project root:**
```bash
cd /Users/adamnielsen/Documents/hackaton/flavour_graph
python run_interactive.py
```

**Lösning 2 - Installera paketet:**
```bash
pip install -e .
python run_interactive.py  # Fungerar nu från vilken mapp som helst
```

## Virtual Environment Problem

### Problem: Virtual environment inte aktiverad

**Symptom:**
- Commands funkar inte
- Import errors
- Fel Python version

**Lösning:**
```bash
# Kontrollera om venv är aktiverad (ska visa (venv) i prompt)
which python  # Ska peka på venv/bin/python

# Om inte aktiverad:
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Problem: Virtual environment korrupt

**Lösning - Skapa om:**
```bash
# Ta bort gammal venv
rm -rf venv

# Skapa ny
python3 -m venv venv
source venv/bin/activate

# Installera dependencies
pip install -r requirements.txt
pip install -e .
```

## Git och data files

### Problem: Stora filer i git

**Lösning:**
```bash
# Kontrollera .gitignore
cat .gitignore

# Ta bort filer från git (men behåll lokalt)
git rm --cached data/*.parquet
git rm --cached data/*.pkl
git commit -m "Remove large data files from git"
```

## Package Building

### Problem: Build errors

**Lösning:**
```bash
# Uppdatera build tools
pip install --upgrade pip setuptools wheel build

# Clean build
rm -rf build/ dist/ *.egg-info
python -m build
```

## Development Tips

### Verify Installation
```bash
# Test all imports
python -c "from src.core import setup_graph; print('✅ Works!')"

# Check package version
python -c "import src; print(src.__version__)"

# List installed packages
pip list | grep flavour
```

### Reload efter ändringar

Med `pip install -e .` är paketet i "editable mode" - ändringar i koden reflekteras direkt utan reinstallation.

Men om du ändrar `setup.py` eller `pyproject.toml`:
```bash
pip install -e . --force-reinstall --no-deps
```

## VS Code Settings

Skapa `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.analysis.extraPaths": [
        "${workspaceFolder}/src"
    ],
    "python.analysis.typeCheckingMode": "basic",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true
}
```

## Quick Fixes

### Reset everything
```bash
# Full reset (nuclear option)
rm -rf venv build dist *.egg-info
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### Update all packages
```bash
pip install --upgrade -r requirements.txt
```

### Check Python path
```bash
python -c "import sys; print('\n'.join(sys.path))"
```

## Common Commands

```bash
# Install in editable mode (development)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Build distribution
python -m build

# Check package info
pip show flavour-graph

# Uninstall
pip uninstall flavour-graph
```

## Getting Help

Om problem kvarstår:
1. Kontrollera Python version: `python --version` (borde vara 3.8+)
2. Kontrollera pip version: `pip --version`
3. Kontrollera venv är aktiverad: `which python`
4. Läs error messages noggrant
5. Kolla logs i `pip install -v -e .` (verbose mode)
