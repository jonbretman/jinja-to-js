from setuptools import setup, find_packages

setup(
    name='jinja-to-js',
    version='0.0.2',
    description="Turns Jinja templates into Underscore templates that can be run in the browser.",
    keywords='jinja underscore html',
    author='Jon Bretman',
    author_email='jon.bretman@gmail.com',
    url='http://github.com/jonbretman/jinja-to-js/',
    license='Python',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'jinja2',
        'six'
    ],
    entry_points={
        'console_scripts': [
            'jinja_to_js = jinja_to_js.__main__:main',
        ]
    }
)
