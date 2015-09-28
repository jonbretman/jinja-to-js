from setuptools import setup, find_packages

setup(
    name='jinja-to-js',
    version='2.0.0',
    description="Turns Jinja templates into JavaScript functions that can be run in the browser.",
    keywords='jinja html javascript templating',
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
