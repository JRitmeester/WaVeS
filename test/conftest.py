"""
This file is used to add the project root to the Python path for all tests in this directory and subdirectories.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))