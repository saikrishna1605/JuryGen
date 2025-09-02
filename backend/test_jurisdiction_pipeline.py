"""
Test script for the jurisdiction-aware analysis pipeline.

This script validates the integration of jurisdiction analysis into the
document processing workflow.
"""

import asyncio
import logging
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pipeline_structure():
    """Test that the jurisdiction-aware pipeline components exist."""
    
    # Test 1: Check jurisdiction analysis service exists
    service_file = os.path.join(os.path.dirname(__file__), 'app', 'services', 'jurisdiction_analysis.py')
    if not os.path.exists(service_file):
        logger.error("❌ Jurisdiction analysis service not found")
        return False
    
    logger.info("✓ Jurisdiction analysis service exists")
    
    # Test 2: Check API endpoints exist
    api_file = os.path.join(os.path.dirname(__file__), 'app', 'api', 'v1', 'endpoints', 'jurisdiction.py')
    if not os.path.exists(api_file):
        logger.error("❌ Jurisdiction API endpoints not found")
        return False
    
    logger.info("✓ Jurisdiction API endpoints exist")
    
    # Test 3: Check crew coordinator integration
    crew_file = os.path.join(os.path.dirname(__file__), 'app', 'agents', 'crew_coordinator.py')
    with open(crew_file, 'r', encoding='utf-8') as f:
        crew_content = f.read()
    
    required_integrations = [
        'JurisdictionDataAgent',
        'jurisdiction_specialist',
        'jurisdiction_context',
        'jurisdiction_compliance'
    ]
    
    missing_integrations = []
    for integration in required_integrations:
        if integration not in crew_content:
            missing_integrations.append(integration)
    
    if missing_integrations:
        logger.error(f"❌ Missing crew coordinator integrations: {missing_integrations}")
        return False
    
    logger.info("✓ Crew coordinator properly integrated with jurisdiction analysis")
    
    # Test 4: Check API router integration
    router_file = os.path.join(os.path.dirname(__file__), 'app', 'api', 'v1', 'router.py')
    with open(router_file, 'r', encoding='utf-8') as f:
        router_content = f.read()
    
    if 'jurisdiction.router' not in router_content:
        logger.error("❌ Jurisdiction router not integrated into main API router")
        return False
    
    logger.info("✓ Jurisdiction router properly integrated")
    
    return True


def test_service_structure():
    """Test the structure of the jurisdiction analysis service."""
    
    service_file = os.path.join(os.path.dirname(__file__), 'app', 'services', 'jurisdiction_analysis.py')
    
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_methods = [
        'class JurisdictionAnalysisService',
        'enhance_document_analysis',
        'analyze_multi_jurisdiction_conflicts',
        'get_jurisdiction_safe_alternatives',
        'validate_jurisdiction_compliance',
        '_get_cached_jurisdiction_context',
        '_enhance_clauses_with_jurisdiction'
    ]
    
    missing_methods = []
    for method in required_methods:
        if method not in content:
            missing_methods.append(method)
    
    if missing_methods:
        logger.error(f"❌ Missing service methods: {missing_methods}")
        return False
    
    logger.info("✓ All required service methods found")
    
    # Check for caching implementation
    if '_context_cache' not in content:
        logger.error("❌ Context caching not implemented")
        return False
    
    logger.info("✓ Context caching implemented")
    
    return True


def test_api_endpoints():
    """Test the structure of jurisdiction API endpoints."""
    
    api_file = os.path.join(os.path.dirname(__file__), 'app', 'api', 'v1', 'endpoints', 'jurisdiction.py')
    
    with open(api_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_endpoints = [
        '@router.get("/context"',
        '@router.post("/compliance"',
        '@router.post("/multi-jurisdiction"',
        '@router.post("/safer-alternatives"',
        '@router.post("/enhance-document"',
        '@router.get("/supported-jurisdictions"'
    ]
    
    missing_endpoints = []
    for endpoint in required_endpoints:
        if endpoint not in content:
            missing_endpoints.append(endpoint)
    
    if missing_endpoints:
        logger.error(f"❌ Missing API endpoints: {missing_endpoints}")
        return False
    
    logger.info("✓ All required API endpoints found")
    
    # Check for proper request/response models
    required_models = [
        'JurisdictionContextRequest',
        'ComplianceAnalysisRequest',
        'MultiJurisdictionRequest',
        'SaferAlternativesRequest'
    ]
    
    missing_models = []
    for model in required_models:
        if model not in content:
            missing_models.append(model)
    
    if missing_models:
        logger.error(f"❌ Missing request/response models: {missing_models}")
        return False
    
    logger.info("✓ All required request/response models found")
    
    return True


def test_pipeline_integration():
    """Test the integration of jurisdiction analysis into the processing pipeline."""
    
    crew_file = os.path.join(os.path.dirname(__file__), 'app', 'agents', 'crew_coordinator.py')
    
    with open(crew_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test 1: Check jurisdiction agent initialization
    if 'self.jurisdiction_agent = JurisdictionDataAgent()' not in content:
        logger.error("❌ Jurisdiction agent not initialized in crew coordinator")
        return False
    
    logger.info("✓ Jurisdiction agent properly initialized")
    
    # Test 2: Check task pipeline modifications
    pipeline_checks = [
        'task_id="jurisdiction_context"',
        'task_id="jurisdiction_compliance"',
        'agent_name="jurisdiction_specialist"'
    ]
    
    missing_pipeline_elements = []
    for check in pipeline_checks:
        if check not in content:
            missing_pipeline_elements.append(check)
    
    if missing_pipeline_elements:
        logger.error(f"❌ Missing pipeline elements: {missing_pipeline_elements}")
        return False
    
    logger.info("✓ Pipeline properly modified for jurisdiction analysis")
    
    # Test 3: Check task execution logic
    execution_checks = [
        'elif agent_name == "jurisdiction_specialist"',
        'get_jurisdiction_context',
        'analyze_clause_jurisdiction_compliance'
    ]
    
    missing_execution_elements = []
    for check in execution_checks:
        if check not in content:
            missing_execution_elements.append(check)
    
    if missing_execution_elements:
        logger.error(f"❌ Missing execution elements: {missing_execution_elements}")
        return False
    
    logger.info("✓ Task execution logic properly implemented")
    
    return True


def test_configuration_updates():
    """Test that configuration has been updated for jurisdiction analysis."""
    
    config_file = os.path.join(os.path.dirname(__file__), 'app', 'core', 'config.py')
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_configs = [
        'BIGQUERY_DATASET_ID',
        'BIGQUERY_STATUTES_TABLE',
        'BIGQUERY_REGULATIONS_TABLE',
        'BIGQUERY_PRECEDENTS_TABLE',
        'BIGQUERY_LOCATION'
    ]
    
    missing_configs = []
    for config in required_configs:
        if config not in content:
            missing_configs.append(config)
    
    if missing_configs:
        logger.error(f"❌ Missing BigQuery configurations: {missing_configs}")
        return False
    
    logger.info("✓ BigQuery configurations properly added")
    
    # Check requirements.txt
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements_content = f.read()
    
    if 'google-cloud-bigquery' not in requirements_content:
        logger.error("❌ BigQuery dependency not found in requirements.txt")
        return False
    
    logger.info("✓ BigQuery dependency properly added")
    
    return True


def test_workflow_enhancements():
    """Test that the workflow has been enhanced with jurisdiction awareness."""
    
    # Test task dependencies
    crew_file = os.path.join(os.path.dirname(__file__), 'app', 'agents', 'crew_coordinator.py')
    
    with open(crew_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that jurisdiction tasks are properly integrated into dependencies
    dependency_checks = [
        '["jurisdiction_context"]',
        'dependencies=["clause_analysis", "jurisdiction_context"]',
        'dependencies=["clause_analysis", "summarization"]'
    ]
    
    found_dependencies = 0
    for check in dependency_checks:
        if check in content:
            found_dependencies += 1
    
    if found_dependencies < 2:  # At least 2 dependency integrations should be found
        logger.error("❌ Jurisdiction tasks not properly integrated into task dependencies")
        return False
    
    logger.info("✓ Jurisdiction tasks properly integrated into workflow dependencies")
    
    # Check conditional task creation
    if 'if jurisdiction else None' not in content:
        logger.error("❌ Conditional jurisdiction task creation not implemented")
        return False
    
    logger.info("✓ Conditional jurisdiction task creation implemented")
    
    # Check task filtering
    if 'tasks = [task for task in tasks if task is not None]' not in content:
        logger.error("❌ Task filtering for None tasks not implemented")
        return False
    
    logger.info("✓ Task filtering properly implemented")
    
    return True


def main():
    """Run all tests for the jurisdiction-aware analysis pipeline."""
    logger.info("Testing Jurisdiction-Aware Analysis Pipeline...")
    logger.info("=" * 60)
    
    tests = [
        ("Pipeline Structure", test_pipeline_structure),
        ("Service Structure", test_service_structure),
        ("API Endpoints", test_api_endpoints),
        ("Pipeline Integration", test_pipeline_integration),
        ("Configuration Updates", test_configuration_updates),
        ("Workflow Enhancements", test_workflow_enhancements)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\nTesting {test_name}...")
        logger.info("-" * 40)
        
        try:
            if test_func():
                logger.info(f"✅ {test_name} - PASSED")
                passed_tests += 1
            else:
                logger.error(f"❌ {test_name} - FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} - ERROR: {str(e)}")
    
    logger.info("=" * 60)
    logger.info(f"Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All tests passed! Jurisdiction-aware analysis pipeline is properly implemented.")
        return True
    else:
        logger.error(f"❌ {total_tests - passed_tests} tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)