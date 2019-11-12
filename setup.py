import setuptools

import council_data as council

setuptools.setup(
    name='council',
    version=council.__version__,
    url=council.__url__,
    author=council.__author__,
    packages=['council', 'council_data'],
    python_requires='>=3.8.0',
    include_package_data=True,
    data_files=[
        ('', ['README.md', 'CHANGELOG.md']),
    ],
    install_requires=[],
)
