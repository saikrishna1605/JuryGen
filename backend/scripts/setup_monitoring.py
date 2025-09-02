#!/usr/bin/env python3
"""
Setup script for Cloud Monitoring infrastructure.

This script sets up:
- Custom metric descriptors
- Monitoring dashboards
- Alert policies
- Notification channels
"""

import asyncio
import sys
import os
from typing import List, Dict

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.monitoring.dashboards import dashboard_manager
from app.monitoring.alerts import alert_manager
from app.services.monitoring import monitoring_service
from app.core.config import get_settings

settings = get_settings()


async def setup_notification_channels() -> List[str]:
    """Set up notification channels for alerts."""
    channels = []
    
    try:
        # Set up email notification if configured
        if hasattr(settings, 'ALERT_EMAIL') and settings.ALERT_EMAIL:
            email_channel = await alert_manager.setup_email_notification_channel(
                settings.ALERT_EMAIL
            )
            channels.append(email_channel)
            print(f"✓ Created email notification channel: {settings.ALERT_EMAIL}")
        
        # Set up Slack notification if configured
        if hasattr(settings, 'SLACK_WEBHOOK_URL') and settings.SLACK_WEBHOOK_URL:
            slack_channel = await alert_manager.setup_slack_notification_channel(
                settings.SLACK_WEBHOOK_URL
            )
            channels.append(slack_channel)
            print("✓ Created Slack notification channel")
        
        if not channels:
            print("⚠ No notification channels configured. Alerts will be created but won't send notifications.")
            print("  Configure ALERT_EMAIL or SLACK_WEBHOOK_URL in your environment to enable notifications.")
        
        return channels
        
    except Exception as e:
        print(f"✗ Error setting up notification channels: {e}")
        return []


async def setup_dashboards() -> Dict[str, str]:
    """Set up monitoring dashboards."""
    try:
        print("Setting up monitoring dashboards...")
        dashboards = await dashboard_manager.setup_all_dashboards()
        
        print("✓ Created dashboards:")
        for name, dashboard_id in dashboards.items():
            print(f"  - {name}: {dashboard_id}")
        
        return dashboards
        
    except Exception as e:
        print(f"✗ Error setting up dashboards: {e}")
        return {}


async def setup_alerts(notification_channels: List[str]) -> Dict[str, str]:
    """Set up alert policies."""
    try:
        print("Setting up alert policies...")
        alerts = await alert_manager.setup_all_alerts(notification_channels)
        
        print("✓ Created alert policies:")
        for name, alert_id in alerts.items():
            print(f"  - {name}: {alert_id}")
        
        return alerts
        
    except Exception as e:
        print(f"✗ Error setting up alerts: {e}")
        return {}


async def initialize_custom_metrics():
    """Initialize custom metric descriptors."""
    try:
        print("Initializing custom metrics...")
        await monitoring_service._initialize_custom_metrics()
        print("✓ Custom metrics initialized")
        
    except Exception as e:
        print(f"✗ Error initializing custom metrics: {e}")


async def verify_setup():
    """Verify that monitoring setup is working."""
    try:
        print("Verifying monitoring setup...")
        
        # Test health checks
        health_results = await monitoring_service.run_health_checks()
        print(f"✓ Health checks working: {health_results['overall_status']}")
        
        # Test metric recording
        await monitoring_service.record_metric(
            metric_type="custom.googleapis.com/ai_legal_companion/setup_test",
            value=1.0,
            labels={"test": "setup_verification"}
        )
        print("✓ Metric recording working")
        
        # Test error reporting
        test_error = Exception("Test error for monitoring setup verification")
        await monitoring_service.report_error(
            error=test_error,
            context={"test": "setup_verification"}
        )
        print("✓ Error reporting working")
        
        print("✓ Monitoring setup verification completed successfully")
        
    except Exception as e:
        print(f"✗ Error during verification: {e}")


async def main():
    """Main setup function."""
    print("🚀 Setting up AI Legal Companion monitoring infrastructure...")
    print(f"Project ID: {settings.GOOGLE_CLOUD_PROJECT}")
    print(f"Location: {settings.VERTEX_AI_LOCATION}")
    print()
    
    try:
        # Initialize custom metrics first
        await initialize_custom_metrics()
        print()
        
        # Set up notification channels
        notification_channels = await setup_notification_channels()
        print()
        
        # Set up dashboards
        dashboards = await setup_dashboards()
        print()
        
        # Set up alerts
        alerts = await setup_alerts(notification_channels)
        print()
        
        # Verify setup
        await verify_setup()
        print()
        
        print("🎉 Monitoring setup completed successfully!")
        print()
        print("Next steps:")
        print("1. Visit the Google Cloud Console to view your dashboards")
        print("2. Configure notification channels if not already done")
        print("3. Test alerts by triggering threshold conditions")
        print("4. Start the monitoring loop in your application")
        print()
        print("Dashboard URLs:")
        print(f"- Cloud Monitoring: https://console.cloud.google.com/monitoring/dashboards?project={settings.GOOGLE_CLOUD_PROJECT}")
        print(f"- Error Reporting: https://console.cloud.google.com/errors?project={settings.GOOGLE_CLOUD_PROJECT}")
        print(f"- Logging: https://console.cloud.google.com/logs?project={settings.GOOGLE_CLOUD_PROJECT}")
        
    except Exception as e:
        print(f"✗ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())