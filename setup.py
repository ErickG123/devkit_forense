from setuptools import setup, find_packages

setup(
    name="forensic_cli",
    version="1.2.11",
    author="Erick Gabriel",
    author_email="erickgabrielalves0@gmail.com",
    description="Toolkit modular para análise de evidências digitais",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ErickG123/devkit_forense",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
)
