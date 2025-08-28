"""
Setup configuration for tree-creator package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the English README
this_directory = Path(__file__).parent
readme_path = this_directory / "README.md"
long_description = readme_path.read_text(encoding="utf-8")
version = __import__("tree_creator._version").__version__

setup(
    name="tree-creator",
    version=version,
    author="Jack3Low",
    author_email="xapa.pw@gmail.com",
    description="Create directory and file structures from tree-like text representations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jack-low/tree-creator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Filesystems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
            "pre-commit>=3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tree-creator=tree_creator.core:main",
        ],
    },
    include_package_data=True,
    license="MIT",
    keywords="tree directory structure filesystem generator creator",
    project_urls={
        "Bug Reports": "https://github.com/jack-low/tree-creator/issues",
        "Source": "https://github.com/jack-low/tree-creator",
        "Documentation": "https://github.com/jack-low/tree-creator#readme",
        "Japanese README": "https://github.com/jack-low/tree-creator/blob/main/README.ja.md",
    },
)
