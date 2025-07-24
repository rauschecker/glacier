import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name='glacier',
    version='0.1.0',
    py_modules=['glacier', 'openai_client'],
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'glacier = glacier:main',
        ],
    },
)
