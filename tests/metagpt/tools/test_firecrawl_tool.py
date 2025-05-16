#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : Tests for Firecrawl Tool

import os
import pytest
from unittest.mock import patch, MagicMock

from metagpt.tools.firecrawl_tool import FirecrawlTool
from metagpt.tools.firecrawl_env import FirecrawlEnv


@pytest.fixture
def firecrawl_tool():
    """Create a FirecrawlTool instance for testing."""
    with patch.dict(os.environ, {'FIRECRAWL_API_KEY': 'test_api_key'}):
        return FirecrawlTool()


@pytest.mark.asyncio
async def test_map_url(firecrawl_tool):
    """Test the map_url method."""
    mock_response = {
        "success": True,
        "links": ["http://example.com/1", "http://example.com/2"]
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        result = await firecrawl_tool.map_url("http://example.com")
        assert result == mock_response
        assert firecrawl_tool.env.current_operation == "map_url"
        assert firecrawl_tool.env.operation_status == "completed"


@pytest.mark.asyncio
async def test_scrape_url(firecrawl_tool):
    """Test the scrape_url method."""
    mock_response = {
        "success": True,
        "data": {"title": "Test Page", "content": "Test Content"}
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        result = await firecrawl_tool.scrape_url("http://example.com")
        assert result == mock_response
        assert firecrawl_tool.env.current_operation == "scrape_url"
        assert firecrawl_tool.env.operation_status == "completed"


@pytest.mark.asyncio
async def test_search(firecrawl_tool):
    """Test the search method."""
    mock_response = {
        "success": True,
        "data": [
            {"title": "Result 1", "url": "http://example.com/1"},
            {"title": "Result 2", "url": "http://example.com/2"}
        ]
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        result = await firecrawl_tool.search("test query")
        assert result == mock_response
        assert firecrawl_tool.env.current_operation == "search"
        assert firecrawl_tool.env.operation_status == "completed"


@pytest.mark.asyncio
async def test_crawl_url(firecrawl_tool):
    """Test the crawl_url method."""
    mock_response = {
        "success": True,
        "id": "test_job_id"
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        result = await firecrawl_tool.crawl_url("http://example.com")
        assert result == mock_response
        assert firecrawl_tool.env.current_operation == "crawl_url"
        assert firecrawl_tool.env.operation_status == "completed"
        assert "test_job_id" in firecrawl_tool.env.active_jobs
        assert firecrawl_tool.env.active_jobs["test_job_id"] == "crawl"


@pytest.mark.asyncio
async def test_get_crawl_status(firecrawl_tool):
    """Test the get_crawl_status method."""
    mock_response = {
        "success": True,
        "status": "completed",
        "data": {"pages": 10}
    }
    
    firecrawl_tool.env.track_job("test_job_id", "crawl")
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        result = await firecrawl_tool.get_crawl_status("test_job_id")
        assert result == mock_response
        assert firecrawl_tool.env.current_operation == "get_crawl_status"
        assert firecrawl_tool.env.operation_status == "completed"
        assert "test_job_id" not in firecrawl_tool.env.active_jobs


@pytest.mark.asyncio
async def test_extract(firecrawl_tool):
    """Test the extract method."""
    mock_response = {
        "success": True,
        "id": "test_job_id"
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response
        
        result = await firecrawl_tool.extract(["http://example.com"])
        assert result == mock_response
        assert firecrawl_tool.env.current_operation == "extract"
        assert firecrawl_tool.env.operation_status == "completed"
        assert "test_job_id" in firecrawl_tool.env.active_jobs
        assert firecrawl_tool.env.active_jobs["test_job_id"] == "extract"


@pytest.mark.asyncio
async def test_get_extract_status(firecrawl_tool):
    """Test the get_extract_status method."""
    mock_response = {
        "success": True,
        "status": "completed",
        "data": {"extracted": 5}
    }
    
    firecrawl_tool.env.track_job("test_job_id", "extract")
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        result = await firecrawl_tool.get_extract_status("test_job_id")
        assert result == mock_response
        assert firecrawl_tool.env.current_operation == "get_extract_status"
        assert firecrawl_tool.env.operation_status == "completed"
        assert "test_job_id" not in firecrawl_tool.env.active_jobs


@pytest.mark.asyncio
async def test_error_handling(firecrawl_tool):
    """Test error handling in the tool."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 500
        mock_post.return_value.json.return_value = {"error": "Internal Server Error"}
        
        with pytest.raises(Exception):
            await firecrawl_tool.map_url("http://example.com")
        
        assert firecrawl_tool.env.operation_status == "failed"


def test_missing_api_key():
    """Test initialization without API key."""
    with pytest.raises(ValueError):
        FirecrawlTool() 