from setuptools import setup, find_packages

setup(
    name="mute_streamer_overload",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "keyboard",
        "flask",
        "flask-socketio",
    ],
    extras_require={
        'dev': [
            'pyinstaller',
            'pytest',
            'cairosvg',
            'pillow',
        ],
    },
    entry_points={
        "console_scripts": [
            "mute-streamer-overload=mute_streamer_overload.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for creating animated text overlays for streamers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
) 