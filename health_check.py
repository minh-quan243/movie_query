#!/usr/bin/env python3
"""
Health Check Script for Movie Query Application
Tests all critical endpoints and dependencies
"""

import sys
import requests
from urllib.parse import urljoin

def test_endpoint(base_url, endpoint, description):
    """Test a single endpoint"""
    url = urljoin(base_url, endpoint)
    try:
        response = requests.get(url, timeout=10)
        status = "✅" if response.status_code == 200 else "❌"
        print(f"{status} {description}")
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"   Response: {list(data.keys())[:5]}")
                elif isinstance(data, list):
                    print(f"   Response: List with {len(data)} items")
            except:
                print(f"   Response: {response.text[:100]}")
        print()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ {description}")
        print(f"   URL: {url}")
        print(f"   Error: {str(e)}")
        print()
        return False

def main():
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    
    print("=" * 60)
    print(f"Testing Movie Query Application")
    print(f"Base URL: {base_url}")
    print("=" * 60)
    print()
    
    results = []
    
    # Test frontend
    print("Frontend Tests")
    print("-" * 60)
    results.append(test_endpoint(base_url, "/", "Frontend Root"))
    print()
    
    # Test API endpoints
    print("API Tests")
    print("-" * 60)
    results.append(test_endpoint(base_url, "/api/health", "Health Check"))
    results.append(test_endpoint(base_url, "/api/genres", "Get Genres"))
    results.append(test_endpoint(base_url, "/api/movies/top-rated?limit=5", "Top Rated Movies"))
    results.append(test_endpoint(base_url, "/api/search?query=inception", "Search Movies"))
    results.append(test_endpoint(base_url, "/api/movies/genre/Action?limit=5", "Movies by Genre"))
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
