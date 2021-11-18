from setuptools import setup

setup(
    name="fastapi-cloud-tasks",
    version="0.0.1",
    description="Trigger delayed Cloud Tasks from FastAPI",
    licesnse="MIT",
    packages=["fastapi_cloud_tasks"],
    install_requires=["google-cloud-tasks", "fastapi"],
    test_requires=[],
    zip_safe=False,
)
