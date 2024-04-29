from setuptools import setup, find_namespace_packages

with open('README.rst', 'r') as fh:
    long_description = fh.read()

setup(
    name='ibdgc-db',
    version='0.0.1',
    author='Phil Schumm',
    author_email='pschumm@uchicago.edu',
    description='Tools for managing information on IBDGC research participants',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://rcg.bsd.uchicago.edu/gitlab/ibdgc/dcc/ibdgc-db',
    packages=find_namespace_packages(where='.'),
    install_requires=[
        'sqlalchemy~=2.0.25',
        'click-config-file~=0.6.0',
        'dataforge[redcap] @ git+https://gitlab.com/pschumm/data-forge.git@c46c2f483f6cca4007c85d4d10b9ef3edb29cef8',
        'eralchemy2~=1.3.8'
    ],
    include_package_data=True,
    entry_points='''
        [console_scripts]
        ibdgc-db=ibdgc_db.cli:cli
    ''',
)
