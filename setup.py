from setuptools import setup
setup(
  name = 'stmoab',
  packages = ['stmoab'],
  version = '0.0.9',
  description = 'A tool for automating a/b testing analysis using stmo dashboards (https://sql.telemetry.mozilla.org)',
  author = 'Marina Samuel',
  author_email = 'msamuel@mozilla.com',
  url = 'https://github.com/mozilla/stmoab',
  keywords = ['stmo', 'redash', 'experiments', 'a/b tests'],
  classifiers = [],
  install_requires=[
    "boto3 == 1.4.4",
    "scipy == 1.0.0",
    "statistics == 1.0.3.5",
    "statsmodels == 0.9.0",
    "urllib3 == 1.24.2",
    "redash_client == 0.2.7"
  ]
)