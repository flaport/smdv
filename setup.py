from setuptools import setup

with open("readme.md", "r") as f:
    long_description = f.read()

setup(
    name="smdv",
    version="0.0.0",
    author="Floris Laporte",
    author_email="floris.laporte@gmail.com",
    description="a simple markdown viewer for linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/flaport/smdv",
    py_modules=["smdv"],
    entry_points={"console_scripts": ["smdv = smdv:main"]},
    python_requires=">=3.6",
    classifiers=[
        "Topic :: Utilities",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
