from setuptools import setup, find_namespace_packages


def read_requirements():
    with open('requirements.txt', 'r') as file:
        return [line.strip() for line in file.readlines()]


setup(
    name='id-search',
    version='0.1.0',
    description='IBDGC ID Database Search Tool',
    long_description_content_type='text/markdown',
    url='https://github.com/ibdgc/id-search',
    author='Christopher Tastad',
    author_email='christopher.tastad@mssm.edu',
    license='MIT',
    packages=find_namespace_packages(where='.'),
    install_requires=read_requirements(),
    include_package_data=True,  # Ensure package data is included
    entry_points={
        'console_scripts': [
            'id-search=id_search.cli:cli'
        ]
    },
)
