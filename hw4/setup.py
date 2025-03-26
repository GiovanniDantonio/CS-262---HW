from setuptools import setup, find_packages

setup(
    name="distributed_chat",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'grpcio',
        'protobuf',
        'pyyaml',
    ],
)
