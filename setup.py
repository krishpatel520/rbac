"""
Django RBAC Core - Role-Based Access Control for Django
"""
from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = 'A comprehensive Role-Based Access Control (RBAC) system for Django applications with multi-tenant support.'

setup(
    name='django-rbac-core',
    version='0.1.1',
    author='Krish Patel',
    author_email='your.email@example.com',  # Update with your email
    description='A comprehensive Role-Based Access Control (RBAC) system for Django applications with multi-tenant support',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/django-rbac-core',  # Update with your repo URL
    packages=find_packages(exclude=['venv', 'venv.*', '*.tests', '*.tests.*', 'tests.*', 'tests']),
    include_package_data=True,
    install_requires=[
        'Django>=3.2.6,<4.0',
        'psycopg2-binary>=2.9.1',
        'djangorestframework>=3.12.4',
        'drf-spectacular>=0.21.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.8',
    keywords='django rbac role-based-access-control permissions multi-tenant authorization',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/django-rbac-core/issues',
        'Source': 'https://github.com/yourusername/django-rbac-core',
    },
)
