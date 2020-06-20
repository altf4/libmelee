from setuptools import setup, find_packages
setup(
    name = 'melee',
    packages = ['melee'],
    install_requires=['hexdump', 'serial', 'py-ubjson'],
    version = '0.1.0',
    description = 'Open API for making your own Smash Bros: Melee AI',
    author = 'AltF4',
    author_email = 'altf4petro@gmail.com',
    url = 'https://github.com/altf4/libmelee',
    download_url = 'https://github.com/altf4/libmelee/tarball/0.1.0',
    keywords = ['dolphin', 'AI', 'video games', 'melee', 'smash bros'],
    classifiers = [],
    license = "LGPLv3",
    include_package_data=True
)
