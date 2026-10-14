from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ifcclash_plus",
    version="0.4.0",
    author="Jocelin",
    author_email="your.email@example.com",
    description="Extended clash detection rules for IFC models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/IfcClash_Plus",
    # pythonocc-core n'est pas sur PyPI : il doit venir de conda-forge
    # (voir environment.yml / conda/meta.yaml)
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.10",
    install_requires=[
        "ifcopenshell",
        "numpy",
        "trimesh",
        "shapely",
    ],
    extras_require={
        "test": ["pytest", "ifctester"],
        "dev": ["pytest", "ifctester", "black", "flake8"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: CAD",
    ],
)