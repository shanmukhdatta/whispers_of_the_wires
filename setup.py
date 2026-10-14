#!/usr/bin/env python3
"""Setuptools compatibility entrypoint.

All v2 package metadata is defined in pyproject.toml. The original legacy app
can still be launched via python run.py or streamlit run app/main.py.
"""
from setuptools import setup

if __name__ == "__main__":
    setup()
