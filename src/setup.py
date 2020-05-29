from setuptools import setup, find_packages

kwargs = {
    'name': 'tangram',
    'version': '0.3.0',
    'description': 'Tools for schema.org validation against ESIP Science-on-schema.org guidelines',
    'author': 'Dave Vieglais',
    'url': 'https://github.com/datadavev/tangram',
    'license': 'Apache License, Version 2.0',
    'packages': find_packages(),
    'package_data': {},
    'install_requires': [
        'click'
    ],
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    'keywords': (
        'schema.org', 'data', 'dataset',
    ),
    'entry_points': {
        'console_scripts': [
            'tangram=tangram:main'
        ],
    }
}
setup(**kwargs)
