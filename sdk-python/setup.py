from setuptools import setup

setup(
    name="thread-driftwatch",
    version="0.4.0",
    py_modules=["driftwatch"],
    package_dir={"": "."},
    install_requires=["httpx>=0.24.0"],
    description="DriftWatch Python SDK — semantic drift and model staleness monitor. Part of the Thread Suite.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Eugene Dayne Mawuli",
    author_email="bitelance.team@gmail.com",
    url="https://github.com/eugene001dayne/drift-watch",
    license="Apache-2.0",
    python_requires=">=3.8",
)