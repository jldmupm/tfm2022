import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jldm.feddback-sensor-analysis",
    version="0.1.0",
    author="José Luis Doménech",
    author_email="jl.domenech@alumnos.upm.es",
    description="Distributed analysis for CrownSensing/Intelligence that combines user's sentations and environment sensor recording.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jldmupm/tfm2022",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
