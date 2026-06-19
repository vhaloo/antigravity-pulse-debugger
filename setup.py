from setuptools import setup, find_packages

setup(
    name="antigravity-pulse-debugger",
    version="1.0.0",
    description="All-in-one terminal diagnostics, SQLite repair, and zombie cancellation utility for Antigravity profiles.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Valentin Wittwe",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        "console_scripts": [
            "agy-debugger=src.main:main",
        ],
    },
    python_requires=">=3.8",
)
