"""
Test configuration for pytest
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))
