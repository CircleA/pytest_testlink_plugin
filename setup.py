from setuptools import setup


setup(
    name='pytest-testlink-plugin',
    version='0.1.3',
    url='https://github.com/CircleA/pytest_testlink_plugin',
    description='PyTest plugin for reporting in TestLink',
    author='Anton circlea42 Kruglikov',
    author_email='circlea42@ya.ru',
    install_requires=['pytest>=6.0.1', 'pytest-xdist>=2.1.0', 'testlink-api>=0.7.12'],
    packages=['pytest_testlink_plugin'],
    entry_points={'pytest11': ['pytest-testlink-plugin = pytest_testlink_plugin.pytest_testlink_plugin', ], },
)
