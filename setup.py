"""
Setup script for UCP (Universal Context Protocol)
Legacy compatibility wrapper for setuptools
"""

from setuptools import setup

# Read the contents of README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="ucp",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
Setup script for UCP (Universal Context Protocol)
Legacy compatibility wrapper for setuptools
"""

from setuptools import setup

# Read the contents of README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="ucp",
    long_description=long_description,
    long_description_content_type="text/markdown",
)

