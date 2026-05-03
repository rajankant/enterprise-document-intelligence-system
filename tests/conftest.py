import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory"""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_invoice_text():
    """Sample invoice text for testing"""
    return """
    Invoice #INV-2024-001
    Date: 15-01-2024
    Due Date: 15-02-2024
    
    Bill From:
    ABC Corporation
    Email: billing@abc.com
    Phone: +1 (555) 123-4567
    Tax ID: 12-3456789
    
    Bill To:
    XYZ Industries
    
    Description of Services:
    Item 1: Software License - 5 x $200.00 = $1,000.00
    Item 2: Support Services - 1 x $2,000.00 = $2,000.00
    Item 3: Implementation - 40 x $50.00 = $2,000.00
    
    Subtotal: $5,000.00
    Tax (10%): $500.00
    Total Amount: $5,500.00
    
    Payment Terms: Net 30
    """


@pytest.fixture
def sample_job_description_text():
    """Sample job description for testing"""
    return """
    Job Description
    
    Position: Senior AI Engineer
    Company: TechCorp Inc
    Location: San Francisco, CA
    Salary: $150,000 - $200,000
    
    About the Role:
    We are looking for an experienced AI engineer to lead our machine learning initiatives.
    
    Key Responsibilities:
    - Design and implement ML pipelines
    - Lead team of engineers
    - Optimize model performance
    
    Requirements:
    - 5+ years of ML experience
    - Python proficiency
    - Experience with PyTorch or TensorFlow
    - Strong communication skills
    
    Benefits:
    - Competitive salary
    - Health insurance
    - 401(k) matching
    - Remote work options
    """


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
