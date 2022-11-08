from pathlib import Path
from setuptools import setup, find_packages

long_description = Path("README.md").read_text()
reqs = Path("requirements.txt").read_text().strip().splitlines()

pkg = "clone_repos"
setup(
    name=pkg,
    version="0.1.0",
    url="https://github.com/seanbreckenridge/clone-repos",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=("""a basic git repo clone script"""),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(include=[pkg]),
    install_requires=reqs,
    package_data={pkg: ["py.typed"]},
    zip_safe=False,
    keywords="",
    python_requires=">=3.9",
    entry_points={"console_scripts": ["clone-repos = clone_repos.__main__:main"]},
    extras_require={
        "testing": [
            "pytest",
            "mypy",
            "flake8",
        ]
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
