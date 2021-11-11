from setuptools import setup

setup(
    name="gelery",
    version="0.0.1",
    description="Trigger delayed Cloud Tasks from FastAPI",
    licesnse="MIT",
    packages=["gelery"],
    install_requires=["google-cloud-tasks", "fastapi"],
    test_requires=[],
    zip_safe=False,
)
