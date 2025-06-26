#!/usr/bin/env python3
"""
PythonKore - Custom Ragnarok Online Client
Rewritten version of OpenKore in Python

This software is open source, licensed under the GNU General Public
License, version 2.
"""

__version__ = "0.1.0"
__author__ = "PythonKore Development Team"
__website__ = "https://github.com/pythonkore/pythonkore"

# Sequential Thinking Import Order:
# 1. Standard library imports
# 2. Third-party imports  
# 3. Local application imports

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path
PYTHONKORE_ROOT = Path(__file__).parent
SRC_DIR = PYTHONKORE_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

# Version information
NAME = "PythonKore"
VERSION = __version__
WEBSITE = __website__
VERSION_TEXT = f"*** {NAME} {VERSION} - Custom Ragnarok Online Client ***\n***   {WEBSITE}   ***\n"
WELCOME_TEXT = f"Welcome to {NAME}."

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__) 