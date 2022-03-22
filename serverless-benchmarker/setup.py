import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 7):
    sys.exit('ERROR: sb requires Python 3.7+')

setup(
    name='serverless-benchmarker',
    version='0.2.0',
    author='Anonymous',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'fire>=0.3.1,<1',
        'PyYAML>=5.3.1,<6',
        'mergedeep>=1.3.0,<2',
        'networkx>=2.5,<3',
        'more-itertools>=8.8.0,<9',
        # Workload gen
        'stochastic==0.6.0',
        'pandas==1.1.3',
        # AWS
        'boto3>=1.17.0,<2',
        # Additional dependencies for certain benchmarks
        'requests>=2.25.1,<3',
        'scikit-image==0.18.1'
    ],
    # Install via pip install --editable .[dev]
    extras_require={
        'dev': [
            'pytest>=6.1.1,<7',
            'flake8>=3.8.4,<4'
        ]
    },
    entry_points='''
        [console_scripts]
        sb=sb.sb:main
    ''',
    python_requires='>=3.7',
)
