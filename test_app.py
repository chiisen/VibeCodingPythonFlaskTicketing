#!/usr/bin/env python3
"""
Test script for the Flask Ticketing System
This script tests the main functionality of the application
"""

import sys
import os
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_app():
    """Test the Flask application routes"""
    print("🧪 Testing Flask Ticketing System")
    print("=" * 50)

    try:
        # Test if Flask app can be imported
        from app import app, TICKETS, orders
        print("✅ Flask app imported successfully")

        # Test ticket data
        print("✅ Ticket data loaded:")
        for ticket in TICKETS:
            print(f"   - {ticket['name']}: NT$ {ticket['price']}")

        # Test with Flask test client
        with app.test_client() as client:
            # Test home route
            response = client.get('/')
            assert response.status_code == 200
            print("✅ Home route (/) working")

            # Test booking route
            response = client.get('/book')
            assert response.status_code == 200
            print("✅ Booking route (/book) working")

            # Test admin route
            response = client.get('/admin')
            assert response.status_code == 200
            print("✅ Admin route (/admin) working")

            # Test form submission
            test_data = {
                'ticket_type': '1',
                'quantity': '2',
                'name': '測試用戶',
                'phone': '0912345678',
                'email': 'test@example.com'
            }
            response = client.post('/submit', data=test_data)
            assert response.status_code == 302  # Redirect to success page
            print("✅ Form submission working")

            # Check if order was created
            assert len(orders) > 0
            print(f"✅ Order created successfully (Order ID: {orders[-1]['id']})")

            # Test success page
            order_id = orders[-1]['id']
            response = client.get(f'/success?order_id={order_id}')
            assert response.status_code == 200
            print("✅ Success page working")

        print("\n" + "=" * 50)
        print("🎉 All tests passed!")
        print("\n📊 Test Results:")
        print(f"   - Total tickets: {len(TICKETS)}")
        print(f"   - Total orders: {len(orders)}")
        print(f"   - Last order: {orders[-1]['name']} - {orders[-1]['ticket_type']}")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    success = test_flask_app()
    if success:
        print("\n🚀 Application is ready to run!")
        print("   Run: python app.py")
        print("   Visit: http://localhost:5000")
    else:
        print("\n💥 Application has issues that need to be fixed")
        sys.exit(1)
