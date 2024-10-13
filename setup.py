"""
    setup build
"""

from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

VERSION = "1.0.0"
DESCRIPTION = (
    "Update Fabric Workspace From Git Repo using A user with Email And Password"
)
# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="updatefromgit",
    version=VERSION,
    author="Muhammad Samy",
    author_email="muhssamy@gmail.com",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["msal", "azlog"],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'
    keywords=["python", "updatefromgit"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
