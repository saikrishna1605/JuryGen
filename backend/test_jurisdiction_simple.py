"""
Simple test to validate the Jurisdiction Data Agent structure.
"""

import os
import sys

def test_agent_file_structure():
    """Test that the jurisdiction agent file exists and has the right structure."""
    
    agent_file = os.path.join(os.path.dirname(__file__), 'app', 'agents', 'jurisdiction_agent.py')
    
    if not os.path.exists(agent_file):
        print("❌ Jurisdiction agent file not found")
        return False
    
    print("✓ Jurisdiction agent file exists")
    
    # Read the file and check for key components
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_components = [
        'class JurisdictionDataAgent',
        'def get_jurisdiction_context',
        'def analyze_clause_jurisdiction_compliance',
        'def _get_relevant_statutes',
        'def _get_relevant_regulations',
        'def _get_relevant_precedents',
        'def _normalize_jurisdiction',
        'def get_jurisdiction_conflicts',
        'bigquery.Client',
        'GenerativeModel'
    ]
    
    missing_components = []
    for component in required_components:
        if component not in content:
            missing_components.append(component)
    
    if missing_components:
        print(f"❌ Missing components: {missing_components}")
        return False
    
    print("✓ All required components found in jurisdiction agent")
    
    # Check configuration updates
    config_file = os.path.join(os.path.dirname(__file__), 'app', 'core', 'config.py')
    with open(config_file, 'r', encoding='utf-8') as f:
        config_content = f.read()
    
    bigquery_configs = [
        'BIGQUERY_DATASET_ID',
        'BIGQUERY_STATUTES_TABLE',
        'BIGQUERY_REGULATIONS_TABLE',
        'BIGQUERY_PRECEDENTS_TABLE'
    ]
    
    missing_configs = []
    for config in bigquery_configs:
        if config not in config_content:
            missing_configs.append(config)
    
    if missing_configs:
        print(f"❌ Missing BigQuery configurations: {missing_configs}")
        return False
    
    print("✓ BigQuery configurations added to settings")
    
    # Check requirements.txt
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements_content = f.read()
    
    if 'google-cloud-bigquery' not in requirements_content:
        print("❌ BigQuery dependency not found in requirements.txt")
        return False
    
    print("✓ BigQuery dependency added to requirements.txt")
    
    # Check __init__.py updates
    init_file = os.path.join(os.path.dirname(__file__), 'app', 'agents', '__init__.py')
    with open(init_file, 'r', encoding='utf-8') as f:
        init_content = f.read()
    
    if 'JurisdictionDataAgent' not in init_content:
        print("❌ JurisdictionDataAgent not exported from __init__.py")
        return False
    
    print("✓ JurisdictionDataAgent properly exported")
    
    return True


def test_agent_methods():
    """Test the structure of key agent methods."""
    
    agent_file = os.path.join(os.path.dirname(__file__), 'app', 'agents', 'jurisdiction_agent.py')
    
    with open(agent_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test jurisdiction mappings
    if 'jurisdiction_mappings' not in content:
        print("❌ Jurisdiction mappings not found")
        return False
    
    print("✓ Jurisdiction mappings defined")
    
    # Test legal areas
    if 'legal_areas' not in content:
        print("❌ Legal areas mapping not found")
        return False
    
    print("✓ Legal areas mapping defined")
    
    # Test BigQuery table references
    bigquery_tables = ['statutes_table', 'regulations_table', 'precedents_table']
    for table in bigquery_tables:
        if table not in content:
            print(f"❌ {table} reference not found")
            return False
    
    print("✓ BigQuery table references configured")
    
    # Test AI integration
    if 'gemini_model' not in content:
        print("❌ Gemini model integration not found")
        return False
    
    print("✓ Gemini AI integration configured")
    
    return True


def main():
    """Run all tests."""
    print("Testing Jurisdiction Data Agent implementation...")
    print("=" * 50)
    
    structure_test = test_agent_file_structure()
    methods_test = test_agent_methods()
    
    print("=" * 50)
    
    if structure_test and methods_test:
        print("🎉 All tests passed! Jurisdiction Data Agent is properly implemented.")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)