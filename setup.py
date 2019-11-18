import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="meta-info-tools",
    version="0.0.1",
    author="Fawzi Mohamed",
    author_email="fawzi@kitabi.eu",
    description="Tools to handle meta_info",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fawzi/meta-info-tools",
    packages=setuptools.find_packages(include=["meta_info_tools", "meta_info_tools.*"]),
    install_requires=["Markdown>=3.1.1", "pydantic>=0.28"],
    extra_require=["black"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
