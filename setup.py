from setuptools import setup, find_packages
import os

PROJECT_DIR = os.path.dirname(__file__)

setup(
    name='scrapy-s3-cache',
    version='0.0.1',
    packages=find_packages(),
    url='http://github.com/acordiner/scrapy-s3-cache',
    license='GPL v2',
    author='Alister Cordiner',
    author_email='alister@cordiner.net',
    description='Use S3 as a cache backend in Scrapy projects.',
    long_description=open(os.path.join(PROJECT_DIR, 'README.rst')).read(),
    install_requires=[
        'scrapy<1.0.0rc1',
        'boto',
    ],
    tests_require=[
        'moto',
        'pytest',
        'leveldb',
    ],
    test_suite='tests',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
)
