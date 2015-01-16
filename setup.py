from setuptools import setup, find_packages

setup(
    name='jinja-to-js',
    version='0.0.13',
    description="Turns Jinja templates into Underscore templates that can be run in the browser.",
    keywords='jinja underscore html',
    author='Jon Bretman',
    author_email='jon.bretman@gmail.com',
    url='http://github.com/jonbretman/jinja-to-js/',
    license='Python',
    packages=find_packages(),
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False,
    install_requires=[
        'jinja2'
    ]
)
