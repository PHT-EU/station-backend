from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.md") as history_file:
    history = history_file.read()

setup(
    name="pht-station",
    version="0.1",
    author="Michael Graf",
    author_email="michael.graf@uni-tuebingen.de",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    description="Package containing the python code for the PHT station. This includes packages containing the API, CLI"
                "as well as as other utilities for interacting with the PHT station infrastructure.",
    long_description=readme + history,
    long_description_content_type="text/markdown",
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
        "redis",
        "jinja2",
        "pyyaml",
        "click",
        "rich",
        "minio",
        "pht-train-container-library",
        "loguru",
        "psutil",

    ],
    entry_points={
        'console_scripts': [
            'station_ctl = station.ctl.cli:cli',
        ],
    },
    include_package_data=True
    # package_data={
    #     "station.ctl.templates": ["station/ctl/templates/*.tmpl", "station/ctl/templates/traefik/*.tmpl"],
    # }
)
