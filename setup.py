import setuptools  # type: ignore

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cocapi",
    version="2.1.0",
    author="Tony Benoy",
    setup_requires=["wheel"],
    author_email="me@tonybenoy.com",
    description="A python wrapper around clash of clans api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tonybenoy/cocapi",
    install_requires=["httpx"],
    keywords="Clash of Clans SuperCell API COC",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ),
    extras_require={"dev": ["black", "pylint", "mypy", "isort"]},
)
