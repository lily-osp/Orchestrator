"""
Basic tests to verify project setup and CI pipeline functionality.
"""

import pytest
import sys
import os

# Add hal_service to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hal_service'))


def test_project_structure():
    """Test that required project directories exist."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    required_dirs = ['hal_service', 'node_red_config', 'docs', 'tests']
    
    for directory in required_dirs:
        dir_path = os.path.join(base_dir, directory)
        assert os.path.exists(dir_path), f"Directory {directory} should exist"
        assert os.path.isdir(dir_path), f"{directory} should be a directory"


def test_hal_service_import():
    """Test that hal_service package can be imported."""
    try:
        import hal_service
        assert hasattr(hal_service, '__version__')
    except ImportError:
        pytest.fail("hal_service package should be importable")


def test_requirements_file_exists():
    """Test that requirements.txt exists in hal_service."""
    requirements_path = os.path.join(
        os.path.dirname(__file__), '..', 'hal_service', 'requirements.txt'
    )
    assert os.path.exists(requirements_path), "requirements.txt should exist"


def test_ci_config_exists():
    """Test that CI configuration exists."""
    ci_path = os.path.join(
        os.path.dirname(__file__), '..', '.github', 'workflows', 'ci.yml'
    )
    assert os.path.exists(ci_path), "CI configuration should exist"