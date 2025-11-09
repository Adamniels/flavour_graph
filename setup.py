"""Setup script for Flavour Graph package."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
else:
    requirements = []

setup(
    name="flavour-graph",
    version="0.1.0",
    author="Adam Nielsen",
    description="Product graph system for analyzing product relationships using NetworkX and embeddings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Adamniels/flavour_graph",
    packages=find_packages(include=["src", "src.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
            "ipython>=8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flavour-interactive=run_interactive:main",
            "flavour-embeddings=run_embeddings:main",
            "flavour-visualize=run_visualization:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.xlsx", "*.md"],
    },
)
