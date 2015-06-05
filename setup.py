from distutils.core import setup
setup(
    name = "gmshtranslator",
    packages = ["gmshtranslator"],
    version = "0.1",
    description = "gmsh .msh file parser",
    author = "Jose Abell",
    author_email = "info@joseabell.com",
    url = "http://www.joseabell.com",
    download_url = "tbd",
    keywords = ["parsing", "gmsh", "msh", "mesh generation"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Development Status :: Beta",
        "Environment :: Other Environment",
        "Intended Audience :: GMSH Users",
        "License :: GPL",
        "Operating System :: OS Independent",
        "Topic :: TBD",
        "Topic :: TBD2",
        ],
    long_description = """\
gmshtranslator
-------------------------------------

Parser for gmsh `.msh` files.

"""
)