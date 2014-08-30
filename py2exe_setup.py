from distutils.core import setup
import py2exe

setup(options = {"py2exe":{"bundle_files":1, 'compressed':2, 'optimize':2}},
      zipfile=None,
      windows=[{'script':"pevisualer.py",
                'icon_resources':[(1, 'pe.ico')]}])
