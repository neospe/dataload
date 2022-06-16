from setuptools import setup

setup(
   name='dataload',
   version='0.1',
   description='A collection of data set loading functions.',
   author='Stefan Pernes',
   author_email='stefan@pernes.net',
   packages=['dataload'],
   install_requires=['pandas', 'pymongo'],
)
