__author__ = 'zmbq'

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import sys
import numpy

BOOST_ROOT = r'd:\boost\1_59_0\lib64' # Default, Windows only. Override in local_settings for now

try:
    from local_settings import *
except:
    pass

extra_compile_args = []
extra_link_args = []
if sys.platform == 'win32':
    library_dirs = ['../../FastCPPUtils/cmake/Release']
    libraries = ['FastCPPUtils']
    extra_compile_args = ['/Ox']
    # extra_link_args = ['/debug']
elif sys.platform in ['linux', 'linux2']:
    library_dirs = ['../../FastCPPUtils/cmake']
    libraries = ['FastCPPUtils']
    extra_compile_args = ['-fPIC']

setup(
    ext_modules=cythonize(
        [Extension(
            "*",
            ["fast.pyx"],
            language='c++',
            include_dirs=[numpy.get_include(), '../../FastCPPUtils'],
            libraries=libraries,
            library_dirs=library_dirs,
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args)]
    )
)
