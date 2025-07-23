#!/usr/bin/env python3
"""
🧪 EMAIL TESTING SCRIPT
Standalone script to test email configuration without running the full application
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def test_email_configuration():
    """Test email configuration independently"""
    
    print("🧪 EMAIL CONFIGURATION TEST")
    print("=" * 50)
    
    # Import after adding to path
    try:
        from config.email_config import email_config
        from auth.otp_service import OTPService
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the backend directory")
        return
    
    # Check configuration
    print("\n📋 EMAIL CONFIGURATION:")
    config_info = email_config.get_debug_info()
    for key, value in config_info.items():
        print(f"  {key}: {value}")
    
    if not email_config.is_configured():
        print("\n❌ EMAIL NOT CONFIGURED")
        print("Please set SMTP_EMAIL and SMTP_PASSWORD in your .env file")
        return
    
    # Test OTP service
    print("\n🔧 TESTING OTP SERVICE...")
    otp_service = OTPService()
    
    # Test connection
    print("\n⚡ Testing email connection...")
    connection_result = await otp_service.test_email_connection()
    print(f"Connection test: {'✅ SUCCESS' if connection_result['success'] else '❌ FAILED'}")
    if not connection_result['success']:
        print(f"Error: {connection_result['error']}")
        return
    
    # Ask for test email
    test_email = input("\n📧 Enter email address to send test OTP (or press Enter to skip): ").strip()
    
    if test_email:
        print(f"\n📤 Sending test OTP to {test_email}...")
        
        try:
            # Create OTP
            otp_code = await otp_service.create_otp(test_email, "test")
            print(f"📝 Generated OTP: {otp_code}")
            
            # Send email
            email_sent = await otp_service.send_otp_email_async(test_email, otp_code, "test")
            
            if email_sent:
                print("✅ TEST EMAIL SENT SUCCESSFULLY!")
                print(f"Check {test_email} for the OTP: {otp_code}")
            else:
                print("❌ FAILED TO SEND TEST EMAIL")
                print("Check the logs above for specific error details")
                
        except Exception as e:
            print(f"❌ ERROR SENDING TEST EMAIL: {e}")
    
    print("\n🏁 EMAIL TEST COMPLETED")

if __name__ == "__main__":
    print("🚀 Starting email configuration test...")
    try:
        asyncio.run(test_email_configuration())
    except KeyboardInterrupt:
        print("\n⏹️ Test cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
