import pathlib
from setuptools import setup

README = (pathlib.Path(__file__).parent / 'README.md').read_text()

setup(name='awking',
      version='1.1.0',
      description='Make it easier to use Python as an AWK replacement',
      long_description=README,
      long_description_content_type='text/markdown',
      url='https://github.com/adsr303/awking',
      author='Artur de Sousa Rocha',
      author_email='adsr@poczta.onet.pl',
      license='MIT',
      classifiers=[
          'Intended Audience :: Developers',
          'Topic :: Text Processing',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Development Status :: 4 - Beta'
      ],
      py_modules=['awking'],
      test_suite='test_awking')
