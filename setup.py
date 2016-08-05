from setuptools import setup
setup(
    name = 'imqtt',
    version = '0.2.7',
    description = 'Iteractive MQTT packet manipulation shell based on IPython',
    author = 'Shafreeck Sea',
    author_email = 'shafreeck@gmail.com',
    url = 'https://github.com/shafreeck/imqtt',
    keywords = ['mqtt', 'ipython', 'python', 'imqtt', 'mqtt client'],
    classifiers = [],
    py_modules=['imqtt', 'ipshell'],
    scripts= ['imqtt'],
    install_requires=[
        'IPython',
    ],
)
