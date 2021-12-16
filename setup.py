# Third Party Imports
from setuptools import setup

with open("version.txt") as f:
    version = f.read().strip()

with open("README.md", encoding="utf-8") as f:
    long_description = f.read().strip()


setup(
    name="fastapi-cloud-tasks",
    version=version,
    description="Trigger delayed Cloud Tasks from FastAPI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    licesnse="MIT",
    packages=["fastapi_cloud_tasks"],
    install_requires=["google-cloud-tasks", "google-cloud-scheduler", "fastapi"],
    test_requires=[],
    zip_safe=False,
)
