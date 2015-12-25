from distutils.core import setup, Extension

setup (name = 'Matascii',
       version = '1.0',
       description = 'ASCII back-end for matplotlib',
       author="Naoki Nishida",
       author_email="domitry@gmail.com",
       packages = ["matascii"],
       package_data = {"matascii":["*.ipynb"]}
)
