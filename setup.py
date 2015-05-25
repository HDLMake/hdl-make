import ez_setup
ez_setup.use_setuptools()

from setuptools import (setup, find_packages)

exec(open('hdlmake/_version.py').read())

try:
    __version__
except Exception:
    __version__ = "0.0"  # default if for some reason the exec did not work

setup(
   name="hdlmake",
   version=__version__,
   description="Hdlmake generates multi-purpose makefiles for HDL projects management.",
   author="Javier D. Garcia-Lasheras",
   author_email="hdl-make@ohwr.org",
   license="GPLv3",
   url="http://www.ohwr.org/projects/hdl-make",
   packages=find_packages(),
   entry_points={
      'console_scripts': [
         'hdlmake = hdlmake.__main__:main',
         ], 
   },
   include_package_data=True,  # use MANIFEST.in during install
   classifiers=[
      "Development Status :: 5 - Production/Stable",
      "Environment :: Console",
      "Topic :: Utilities",
      "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
      "Topic :: Software Development :: Build Tools",
    ],
   )
