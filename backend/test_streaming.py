#!/usr/bin/env python3
"""
Simple test script for the real-time streaming functionality.

This script tests:
- SSE connection creation
- Job update broadcasting
- Connection management
"""

import asyncio
import json
import logging
from datetime import datetime
from uuid import uuid4

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_streaming_service():
    """Test the streaming service functionality."""
    try:
        # Import the streaming service
        from app.services.realtime_streaming import streaming_service
        
        logger.info("Testing streaming service...")
        
        # Test 1: Get connection stats
        stats = await streaming_service.get_connection_stats()
        logger.info(f"Initial connection stats: {stats}")
        
        # Test 2: Broadcast a test message
        await streaming_service.broadcast_system_message(
            "Test system message",
            "info"
        )
        logger.info("System message broadcasted")
        
        # Test 3: Simulate job update
        test_job_id = str(uuid4())
        test_job_data = {
            "id": test_job_id,
            "user_id": "test_user",
            "status": "processing",
            "current_stage": "analysis",
            "progress_percentage": 50,
            "created_at": datetime.utcnow().isoformat(),
            "message": "Test job update"
        }
        
        await streaming_service.broadcast_job_update(test_job_id, test_job_data)
        logger.info(f"Job update broadcasted for job {test_job_id}")
        
        # Test 4: Get final stats
        final_stats = await streaming_service.get_connection_stats()
        logger.info(f"Final connection stats: {final_stats}")
        
        logger.info("Streaming service test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Streaming service test failed: {str(e)}")
        return False

async def test_job_manager_integration():
    """Test job manager integration with streaming."""
    try:
        from app.services.job_manager import JobManager
        
        logger.info("Testing job manager streaming integration...")
        
        # Create job manager instance
        job_manager = JobManager()
        
        # Test job creation and updates would go here
        # For now, just verify the streaming service is available
        assert hasattr(job_manager, 'streaming_service')
        logger.info("Job manager has streaming service integration")
        
        logger.info("Job manager integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Job manager integration test failed: {str(e)}")
        return False

async def main():
    """Run all streaming tests."""
    logger.info("Starting streaming functionality tests...")
    
    # Test streaming service
    streaming_test = await test_streaming_service()
    
    # Test job manager integration
    job_manager_test = await test_job_manager_integration()
    
    # Summary
    if streaming_test and job_manager_test:
        logger.info("✅ All streaming tests passed!")
    else:
        logger.error("❌ Some streaming tests failed!")
        
    return streaming_test and job_manager_test

if __name__ == "__main__":
    asyncio.run(main())