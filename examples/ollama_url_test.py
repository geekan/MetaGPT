#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Simple test for Ollama URL construction

def get_api_url(base_url, suffix):
    """
    Ensure the API URL is correctly formed by handling both direct Ollama URLs and third-party wrappers.
    For direct Ollama, the URL should be: base_url + /api + suffix
    For wrappers, we need to check if /api is already in the base_url
    """
    base_url = base_url.rstrip('/')
    
    # If base_url already ends with /api, just append the suffix
    if base_url.endswith('/api'):
        return f"{base_url}{suffix}"
    
    # If base_url contains /api/ somewhere in the middle (like in a wrapper URL)
    # we should just append the suffix directly
    if '/api/' in base_url:
        return f"{base_url}{suffix}"
        
    # For standard Ollama URL, insert /api before the suffix
    return f"{base_url}/api{suffix}"

def test_url_construction():
    """Test URL construction with different base URLs"""
    # Test cases
    test_cases = [
        {
            "name": "Direct Ollama URL",
            "base_url": "http://localhost:11434",
            "suffix": "/chat",
            "expected": "http://localhost:11434/api/chat"
        },
        {
            "name": "Wrapper URL with /api at end",
            "base_url": "http://localhost:8989/ollama/api",
            "suffix": "/chat",
            "expected": "http://localhost:8989/ollama/api/chat"
        },
        {
            "name": "Wrapper URL without /api",
            "base_url": "http://localhost:8989/ollama",
            "suffix": "/chat",
            "expected": "http://localhost:8989/ollama/api/chat"
        },
        {
            "name": "Wrapper URL with /api/ in middle",
            "base_url": "http://localhost:8989/api/ollama",
            "suffix": "/chat",
            "expected": "http://localhost:8989/api/ollama/chat"
        }
    ]
    
    # Run tests
    print("Testing Ollama URL construction...")
    print("-" * 50)
    
    for case in test_cases:
        result = get_api_url(case["base_url"], case["suffix"])
        
        print(f"Test: {case['name']}")
        print(f"Base URL: {case['base_url']}")
        print(f"Suffix: {case['suffix']}")
        print(f"Result URL: {result}")
        print(f"Expected: {case['expected']}")
        print(f"{'✅ PASS' if result == case['expected'] else '❌ FAIL'}")
        print("-" * 50)

if __name__ == "__main__":
    test_url_construction()
