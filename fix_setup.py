#!/usr/bin/env python3
"""Fix setup.py for autoresearch package"""

content = '''from setuptools import setup, find_packages

setup(
    name="autoresearch",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
)
'''

with open("setup.py", "w") as f:
    f.write(content)

print("setup.py fixed!")
