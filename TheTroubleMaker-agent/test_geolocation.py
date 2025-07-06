#!/usr/bin/env python3
"""
Test script to verify IP geolocation functionality
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from tools import _geolocate_ip, _extract_location_data

async def test_geolocation():
    """Test IP geolocation functionality"""
    print("🔍 Testing IP Geolocation...")
    
    # Test IPs from various breaches (these are real IPs found in breach data)
    test_ips = ["87.126.40.171", "194.12.225.246", "85.196.134.74"]
    
    print("\n📍 Testing individual IP geolocation:")
    for ip in test_ips:
        print(f"\n🔍 Geolocating {ip}...")
        result = await _geolocate_ip(ip)
        if result.get("success"):
            print(f"✅ {ip} -> {result.get('city', 'Unknown')}, {result.get('country', 'Unknown')}")
            print(f"   ISP: {result.get('isp', 'Unknown')}")
            print(f"   Coordinates: {result.get('latitude')}, {result.get('longitude')}")
        else:
            print(f"❌ Failed to geolocate {ip}: {result.get('error', 'Unknown error')}")
    
    print("\n🌍 Testing location data extraction with geolocation:")
    
    # Create mock breach data with the test IPs
    mock_breach_data = {
        "List": {
            "Test Breach": {
                "Data": [
                    {"IP": "87.126.40.171"},
                    {"IP": "194.12.225.246"},
                    {"IP": "85.196.134.74"}
                ]
            }
        }
    }
    
    location_data = await _extract_location_data(mock_breach_data)
    
    print(f"\n📊 Location Data Summary:")
    print(f"   IPs found: {len(location_data.get('ips', []))}")
    print(f"   IPs geolocated: {len(location_data.get('ip_details', []))}")
    print(f"   Cities: {location_data.get('cities', [])}")
    print(f"   Countries: {location_data.get('countries', [])}")
    
    if location_data.get('ip_details'):
        print(f"\n📍 Geolocated IP Details:")
        for ip_detail in location_data['ip_details']:
            print(f"   • {ip_detail['ip']} -> {ip_detail.get('city', 'Unknown')}, {ip_detail.get('country', 'Unknown')}")
    
    print("\n✅ Geolocation test completed!")

if __name__ == "__main__":
    asyncio.run(test_geolocation()) 