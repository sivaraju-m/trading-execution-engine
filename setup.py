from setuptools import setup, find_packages

setup(
    name="trading-execution-engine",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.5.0",
        "numpy>=1.22.0",
        "kiteconnect>=4.1.0",
        "shared-services>=0.1.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "execution-engine=trading_execution_engine.bin.automated_trading_system:main",
            "live-trading=trading_execution_engine.bin.live_trading_flow:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Trading execution engine for placing and managing orders through various brokers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trading-execution-engine",
)
