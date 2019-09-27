#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
from Cython.Distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
    Extension("main",  ["main.py"]),
    Extension("audio",  ["audio.py"]),
    Extension("peakDetector",  ["peakDetector.py"]),
    Extension("solenoid",  ["solenoid.py"]),
    Extension("OSCserver",  ["OSCserver.py"]),
]

for e in ext_modules : e.cython_directives = {"language_level": "3"}

setup(
    name = 'GMEM-client',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,
)
