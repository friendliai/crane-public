from setuptools import find_packages, setup

setup(
    name="cranecli_plugin_example",
    version="0.1.0",
    url="https://github.com/snuspl/crane",
    license="MIT",

    author="Ahnjae Shin",
    author_email="yuyupopo@snu.ac.kr",

    description="Example plugin package for cranecli",

    packages=find_packages(exclude=("tests",)),

    install_requires=["typer"],

    entry_points={"cranecli.plugins": "example = cranecli_plugin_example"},

    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
