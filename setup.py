from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license_ = f.read()

with open("requirements.txt") as f:
    requirements = f.read().split("\n")

setup(
    name='McScript',
    version='0.1.0',
    packages=find_packages(where="mcscript"),
    url='https://github.com/Inky-developer/McScript',
    license=license_,
    author='inky',
    author_email='developerinky@gmail.com',
    description='A Simple and powerful datapack generator for minecraft',
    long_description=readme,
    install_requires=requirements
)
