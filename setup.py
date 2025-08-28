from setuptools import setup, find_packages

setup(
    name="aralia_openrag",  # 套件名稱
    version="0.2.0",  # 版本號
    author="BigObject",
    author_email="oscarlee@bigobject.io",
    description="OpenRAG is a framework for building RAG applications with LLMs and data planets.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/oscarlee8787/AraliaOpenRAG",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[ 
    ],
)