from setuptools import setup, find_packages

version = '0.0.1'

setup(
    name="chitboxes",
    version=version,
    entry_points={
        'console_scripts': [
            "chitboxes = chitboxes:main"
        ],
    },
    packages=find_packages(exclude=['tests']),
    install_requires=["reportlab>=3.4.0",
                      "Pillow>=4.1.0"],
    url='http://domtabs.sandflea.org',
    include_package_data=True,
    author="Peter Gorniak",
    author_email="sumpfork@mailmight.net",
    description="Chitbox Generation for Board- and Cardgames",
    keywords=['boardgame', 'cardgame', 'chitboxes'],
    long_description=""
)
