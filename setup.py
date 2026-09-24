from setuptools import setup, find_packages

setup(
    name="quilt-linker",
    version="0.1.0",
    description="Brewed by quilt-brewer.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
)
