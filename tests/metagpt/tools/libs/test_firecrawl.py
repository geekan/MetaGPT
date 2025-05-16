#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test module for the Firecrawl tool."""

import os
import pytest
from unittest.mock import MagicMock, patch
import requests

from metagpt.tools.libs.firecrawl import Firecrawl

API_KEY = "YOUR-FIRECRAWL-API-KEY"
API_URL = "https://api.firecrawl.dev"

EXPECTED_HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}',
    'X-Origin': 'metagpt',
    'X-Origin-Type': 'integration',
}

@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"success": True}
    return response

@pytest.fixture
def firecrawl():
    """Create a Firecrawl instance for testing."""
    return Firecrawl(api_key=API_KEY, api_url=API_URL)

def test_initialization():
    """Test initialization with direct parameters."""
    tool = Firecrawl(api_key=API_KEY, api_url=API_URL)
    assert tool.api_key == API_KEY
    assert tool.api_url == API_URL

def test_initialization_with_env_vars():
    """Test initialization with environment variables."""
    os.environ["FIRECRAWL_API_KEY"] = API_KEY
    os.environ["FIRECRAWL_API_URL"] = API_URL
    
    tool = Firecrawl()
    assert tool.api_key == API_KEY
    assert tool.api_url == API_URL
    
    # Clean up environment variables
    del os.environ["FIRECRAWL_API_KEY"]
    del os.environ["FIRECRAWL_API_URL"]

def test_initialization_without_api_key():
    """Test initialization without API key raises error."""
    with pytest.raises(ValueError, match="No API key provided"):
        Firecrawl()

def test_map_url(firecrawl, mock_response):
    """Test the map_url method."""
    mock_response.json.return_value = {"success": True, "links": ["http://example.com/page1"]}
    
    with patch('requests.post', return_value=mock_response) as mock_post:
        result = firecrawl.map_url("http://example.com")
        
        assert result == {"success": True, "links": ["http://example.com/page1"]}
        mock_post.assert_called_once_with(
            f'{API_URL}/v1/map',
            headers=EXPECTED_HEADERS,
            json={'url': 'http://example.com'},
            timeout=60
        )

def test_scrape_url(firecrawl, mock_response):
    """Test the scrape_url method."""
    mock_response.json.return_value = {"success": True, "data": {"title": "Example"}}
    
    with patch('requests.post', return_value=mock_response) as mock_post:
        result = firecrawl.scrape_url("http://example.com")
        
        assert result == {"success": True, "data": {"title": "Example"}}
        mock_post.assert_called_once_with(
            f'{API_URL}/v1/scrape',
            headers=EXPECTED_HEADERS,
            json={'url': 'http://example.com'},
            timeout=60
        )

def test_search(firecrawl, mock_response):
    """Test the search method."""
    mock_response.json.return_value = {"success": True, "results": [{"title": "Test Result"}]}
    
    with patch('requests.post', return_value=mock_response) as mock_post:
        result = firecrawl.search("test query")
        
        assert result == {"success": True, "results": [{"title": "Test Result"}]}
        mock_post.assert_called_once_with(
            f'{API_URL}/v1/search',
            headers=EXPECTED_HEADERS,
            json={'query': 'test query'},
            timeout=60
        )

def test_crawl_url(firecrawl, mock_response):
    """Test the crawl_url method."""
    mock_response.json.return_value = {"success": True, "id": "test_job_id"}
    
    with patch('requests.post', return_value=mock_response) as mock_post:
        result = firecrawl.crawl_url("http://example.com")
        
        assert result == {"success": True, "id": "test_job_id"}
        mock_post.assert_called_once_with(
            f'{API_URL}/v1/crawl',
            headers=EXPECTED_HEADERS,
            json={'url': 'http://example.com'},
            timeout=60
        )

def test_get_crawl_status(firecrawl, mock_response):
    """Test the get_crawl_status method."""
    mock_response.json.return_value = {"success": True, "status": "completed"}
    
    with patch('requests.get', return_value=mock_response) as mock_get:
        result = firecrawl.get_crawl_status("test_job_id")
        
        assert result == {"success": True, "status": "completed"}
        mock_get.assert_called_once_with(
            f'{API_URL}/v1/crawl/test_job_id',
            headers=EXPECTED_HEADERS,
            timeout=60
        )

def test_extract(firecrawl, mock_response):
    """Test the extract method."""
    mock_response.json.return_value = {"success": True, "data": {"extracted": "content"}}
    
    with patch('requests.post', return_value=mock_response) as mock_post:
        result = firecrawl.extract(["http://example.com"])
        
        assert result == {"success": True, "data": {"extracted": "content"}}
        mock_post.assert_called_once_with(
            f'{API_URL}/v1/extract',
            headers=EXPECTED_HEADERS,
            json={'urls': ['http://example.com']},
            timeout=60
        )

def test_get_extract_status(firecrawl, mock_response):
    """Test the get_extract_status method."""
    mock_response.json.return_value = {"success": True, "status": "completed"}
    
    with patch('requests.get', return_value=mock_response) as mock_get:
        result = firecrawl.get_extract_status("test_job_id")
        
        assert result == {"success": True, "status": "completed"}
        mock_get.assert_called_once_with(
            f'{API_URL}/v1/extract/test_job_id',
            headers=EXPECTED_HEADERS,
            timeout=60
        )

def test_error_handling(firecrawl):
    """Test error handling."""
    mock_error_response = MagicMock()
    mock_error_response.status_code = 400
    mock_error_response.json.return_value = {
        "error": "Test error",
        "details": "Test error details"
    }
    
    with patch('requests.post', return_value=mock_error_response):
        with pytest.raises(requests.exceptions.HTTPError) as exc_info:
            firecrawl.map_url("http://example.com")
        
        assert "Test error" in str(exc_info.value)
        assert "Test error details" in str(exc_info.value) 