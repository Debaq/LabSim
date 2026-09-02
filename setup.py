from setuptools import setup, find_namespace_packages

setup(
    name='LabSim',
    version='2024.1',
    author='Debaq',
    author_email='david.avila@uach.cl',
    description='Simulador Virtual de exámenes auditivos y oculares',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Debaq/LabSim',
    packages=find_namespace_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={
        '': ['resources/config/*.json', 'resources/data/*.csv'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        'somepackage>=1.0',
        'anotherpackage>=2.0',
    ],
)
