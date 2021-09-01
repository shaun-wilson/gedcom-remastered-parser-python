from setuptools import setup

setup(
    name='GEDCOM Remastered Parser (Python)',
    url='https://github.com/shaun-wilson/gedcom-remastered-parser-python',
    author='shaun-wilson',
    author_email='47620271+shaun-wilson@users.noreply.github.com',
    packages=['gedcom_remastered_parser'],
    install_requires=[],
    version='0.1.1',
    license='MIT',
    description='A Python 3 package that parses a GEDCOM Remastered Standard, and generates an object model.',
    long_description=open('README.md').read(),
)