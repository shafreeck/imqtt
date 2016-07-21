from distutils.core import setup
setup(
    name = 'imqtt',
    version = '0.1',
    description = 'Iteractive MQTT packet manipulation shell based on IPython',
    author = 'Shafreeck Sea',
    author_email = 'shafreeck@gmail.com',
    url = 'https://github.com/shafreeck/imqtt',
    download_url = 'https://github.com/shafreeck/imqtt/tarball/0.1', 
    keywords = ['mqtt', 'ipython', 'python', 'imqtt', 'mqtt client'],
    classifiers = [],
    py_modules=['imqtt'],
    scripts= ['imqtt'],
    requires=[
        'IPython',
    ],
)
