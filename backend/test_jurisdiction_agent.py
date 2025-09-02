"""
Test script for the Jurisdiction Data Agent.

This script tests the basic functionality of the JurisdictionDataAgent
without requiring a full BigQuery setup.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from unittest.mock import Mock, patch, AsyncMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_jurisdiction_agent():
    """Test the jurisdiction agent with mocked dependencies."""
    
    # Mock BigQuery client
    mock_bq_client = Mock()
    mock_query_job = Mock()
    mock_query_job.result.return_value = []  # Empty results for testing
    mock_bq_client.query.return_value = mock_query_job
    
    # Mock Gemini model
    mock_gemini_response = Mock()
    mock_gemini_response.text = '{"compliance_score": 0.8, "compliance_risk": 0.2, "confidence": 0.9, "recommendations": ["Test recommendation"], "potential_issues": [], "rationale": "Test analysis"}'
    mock_gemini_model = AsyncMock()
    mock_gemini_model.generate_content_async.return_value = mock_gemini_response
    
    # Create agent with mocked dependencies
    with patch('app.agents.jurisdiction_agent.bigquery.Client', return_value=mock_bq_client), \
         patch('app.agents.jurisdiction_agent.GenerativeModel', return_value=mock_gemini_model):
        
        agent = JurisdictionDataAgent()
        
        # Test 1: Get jurisdiction context
        logger.info("Testing jurisdiction context retrieval...")
        try:
            context = await agent.get_jurisdiction_context("CA", "contract")
            logger.info(f"✓ Jurisdiction context retrieved: {context['jurisdiction']}")
            assert context['jurisdiction'] == 'CA'
            assert 'statutes' in context
            assert 'regulations' in context
            assert 'precedents' in context
        except Exception as e:
            logger.error(f"✗ Jurisdiction context test failed: {e}")
            return False
        
        # Test 2: Analyze clause compliance
        logger.info("Testing clause compliance analysis...")
        try:
            test_clause = Clause(
                text="The landlord may terminate this lease at any time with 30 days notice.",
                classification=ClauseClassification.CAUTION,
                risk_score=0.6,
                impact_score=70,
                likelihood_score=40,
                role_analysis={},
                safer_alternatives=[],
                legal_citations=[],
                keywords=[],
                category="termination"
            )
            
            compliance_result = await agent.analyze_clause_jurisdiction_compliance(
                test_clause, "CA", UserRole.TENANT
            )
            
            logger.info(f"✓ Compliance analysis completed: score={compliance_result['compliance_score']}")
            assert 'compliance_score' in compliance_result
            assert 'compliance_risk' in compliance_result
            assert 'recommendations' in compliance_result
        except Exception as e:
            logger.error(f"✗ Compliance analysis test failed: {e}")
            return False
        
        # Test 3: Jurisdiction normalization
        logger.info("Testing jurisdiction normalization...")
        try:
            normalized = agent._normalize_jurisdiction("California")
            assert normalized == "CA"
            logger.info(f"✓ Jurisdiction normalization: 'California' -> '{normalized}'")
            
            normalized = agent._normalize_jurisdiction("New York")
            assert normalized == "NY"
            logger.info(f"✓ Jurisdiction normalization: 'New York' -> '{normalized}'")
        except Exception as e:
            logger.error(f"✗ Jurisdiction normalization test failed: {e}")
            return False
        
        # Test 4: Legal area determination
        logger.info("Testing legal area determination...")
        try:
            area = agent._determine_legal_area("This employment agreement governs the relationship between employer and employee.")
            logger.info(f"✓ Legal area determined: '{area}'")
            assert area == "employment"
            
            area = agent._determine_legal_area("The tenant shall pay rent monthly to the landlord.")
            logger.info(f"✓ Legal area determined: '{area}'")
            assert area == "real_estate"
        except Exception as e:
            logger.error(f"✗ Legal area determination test failed: {e}")
            return False
        
        # Test 5: Legal term extraction
        logger.info("Testing legal term extraction...")
        try:
            terms = agent._extract_legal_terms("This contract may be terminated upon breach of any covenant or warranty.")
            logger.info(f"✓ Legal terms extracted: {terms}")
            assert "contract" in terms
            assert "terminated" in terms or "terminate" in terms
            assert "breach" in terms
        except Exception as e:
            logger.error(f"✗ Legal term extraction test failed: {e}")
            return False
        
        logger.info("🎉 All jurisdiction agent tests passed!")
        return True


async def test_jurisdiction_conflicts():
    """Test jurisdiction conflict analysis."""
    
    # Mock dependencies
    mock_bq_client = Mock()
    mock_query_job = Mock()
    mock_query_job.result.return_value = []
    mock_bq_client.query.return_value = mock_query_job
    
    mock_gemini_response = Mock()
    mock_gemini_response.text = '{"conflicts": [{"type": "choice_of_law", "description": "Different choice of law requirements", "severity": "medium", "affected_areas": ["contracts"], "resolution_approach": "Specify governing law explicitly"}]}'
    mock_gemini_model = AsyncMock()
    mock_gemini_model.generate_content_async.return_value = mock_gemini_response
    
    with patch('app.agents.jurisdiction_agent.bigquery.Client', return_value=mock_bq_client), \
         patch('app.agents.jurisdiction_agent.GenerativeModel', return_value=mock_gemini_model):
        
        agent = JurisdictionDataAgent()
        
        logger.info("Testing jurisdiction conflict analysis...")
        try:
            conflicts = await agent.get_jurisdiction_conflicts("CA", ["NY", "TX"], "contract")
            logger.info(f"✓ Conflict analysis completed: {len(conflicts.get('conflicts', []))} conflicts found")
            assert 'conflicts' in conflicts
            assert 'recommendations' in conflicts
        except Exception as e:
            logger.error(f"✗ Jurisdiction conflict test failed: {e}")
            return False
        
        return True


async def main():
    """Run all tests."""
    logger.info("Starting Jurisdiction Data Agent tests...")
    
    # Test basic functionality
    basic_tests_passed = await test_jurisdiction_agent()
    
    # Test conflict analysis
    conflict_tests_passed = await test_jurisdiction_conflicts()
    
    if basic_tests_passed and conflict_tests_passed:
        logger.info("🎉 All tests completed successfully!")
        return True
    else:
        logger.error("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    asyncio.run(main())