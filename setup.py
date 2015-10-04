from setuptools import setup
import os
import shutil
import locale
locale.getpreferredencoding = lambda: 'UTF-8'
os.putenv('LC_CTYPE','ja_JP.UTF-8')

setup(name="jjfattypy",
      version="0.1",
      description="A chronic array of modules for general input and output, logging, and configuring connections to databases",
      long_description="Prompting users with yes/no, or for lists. Database connections with mysql and sqlite. Regular expressions turned to full-width content",
      author="Colin Hilchey",
      author_email="hilcharge@jjfatty.com",
      license="MIT",
      packages=['jjfattypy'],
      install_requires=['python-dateutil',
                        ],
      include_package_data=True,
      zip_safe=False)

