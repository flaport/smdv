import ast
import tokenize
from setuptools import setup

with tokenize.open("smdv.py") as f:
    module = ast.parse(f.read(), filename=f.name)

metadata = {}
for stmt in module.body:
    match stmt:
        case ast.Assign(targets=[ast.Name(id=name)], value=ast.Constant()):
            metadata[name] = ast.literal_eval(stmt.value)
author = metadata["__author__"]
version = metadata["__version__"]
description = ast.get_docstring(module)

with open("readme.md", "r") as f:
    long_description = f.read()

setup(
    name="smdv",
    version=version,
    author=author,
    author_email="floris.laporte@gmail.com",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/flaport/smdv",
    py_modules=["smdv"],
    entry_points={"console_scripts": ["smdv = smdv:main"]},
    python_requires=">=3.10",
    install_requires=["flask", "websockets"],
    classifiers=[
        "Topic :: Utilities",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
