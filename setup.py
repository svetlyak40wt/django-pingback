from setuptools import setup, find_packages

setup(
    name = 'django-pingback',
    version = '0.1.1',
    description = 'Pingback client/server implementation for Django framework.',
    keywords = 'django apps',
    license = 'New BSD License',
    author = 'Alexander Solovyov',
    author_email = 'piranha@piranha.org.ua',
    maintainer = 'Alexander Artemenko',
    maintainer_email = 'svetlyak.40wt@gmail.com',
    url = 'http://code.google.com/p/django-pingback/',
    install_requires = ['django-xmlrpc>=0.1.0'],
    dependency_links = ['http://pypi.aartemenko.com'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages = find_packages(exclude=['xmlrpc']),
    include_package_data = True,
)

