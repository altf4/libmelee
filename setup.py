from setuptools import setup, find_packages
setup(
    name = 'melee',
    packages = ['melee'],
    install_requires=[
        'pyenet',
        'py-ubjson',
        'numpy',
        'pywin32; platform_system=="Windows"',
        'packaging'
    ],
    version = '0.23.1',
    description = 'Open API written in Python 3 for making your own Smash Bros: Melee AI that works with Slippi Online',
    author = 'AltF4',
    author_email = 'altf4petro@gmail.com',
    url = 'https://github.com/altf4/libmelee',
    download_url = 'https://api.github.com/repos/libmelee/libmelee/tarball',
    keywords = ['dolphin', 'AI', 'video games', 'melee', 'smash bros', 'slippi'],
    classifiers = [],
    license = "LGPLv3",
    include_package_data=True
)
