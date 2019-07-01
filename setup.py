import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cocapi",
    version="1.0.6",
    author="Tony Benoy",
    author_email="me@tonybenoy.com",
    description="A python wrapper around clash of clans api",
    long_description="A python wrapper around clash of clans api",
    long_description_content_type="text/markdown",
    url="https://github.com/tonybenoy/cocapi",
    install_requires=["requests"],
    keywords='Clash of Clans SuperCell API COC',
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ),
)
