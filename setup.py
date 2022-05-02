from setuptools import setup, find_packages

setup(
    name="pht-station",
    version="0.1",
    description="Package containing the python code for the PHT station. This includes packages containing the API, CLI"
                "as well as as other utilities for interacting with the PHT station infrastructure.",
    long_description=open("README.md").read(),
    packages=find_packages(),
    install_requires=[
        "fastapi[all]",
        "pycryptodome",
        "cryptography",
        "uvicorn",
        "python-dotenv",
        "docker",
        "fhir-kindling",
        "pandas",
        "SQLAlchemy",
        "psycopg2-binary",
        "jinja2",
        "pyyaml",
        "click",
        "rich",
        "minio",
        "pht-train-container-library",
        "loguru"

    ],
    entry_points={
        'console_scripts': [
            'station_ctl = station.ctl.cli:cli',
        ],
    },

)
