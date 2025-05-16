#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Firecrawl Tool for MetaGPT.

This module provides a tool for interacting with the Firecrawl API, enabling web scraping,
crawling, searching, and information extraction capabilities.

Author: Ademílson Tonato <ftonato@sideguide.dev | ademilsonft@outlook.com>
"""

import os
from typing import Any, Dict, List, Optional, Union

import requests
from metagpt.tools.tool_registry import register_tool


@register_tool(tags=["web", "scraping", "search"], include_functions=["map_url", "scrape_url", "search", "crawl_url", "extract"])
class Firecrawl:
    """A tool for web scraping, crawling, searching and information extraction using Firecrawl API.
    
    This tool provides methods to interact with the Firecrawl API for various web data collection
    and processing tasks. It supports URL mapping, scraping, searching, crawling, and information
    extraction.

    Attributes:
        api_key (str): The API key for authenticating with Firecrawl API.
        api_url (str): The base URL for the Firecrawl API.
    """

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """Initialize the Firecrawl tool.

        Args:
            api_key (Optional[str]): API key for Firecrawl. Defaults to environment variable.
            api_url (Optional[str]): Base URL for Firecrawl API. Defaults to production URL.
        """
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError('No API key provided')
        self.api_url = api_url or os.getenv('FIRECRAWL_API_URL', 'https://api.firecrawl.dev')
        self.request_timeout = 60

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests.

        Returns:
            Dict[str, str]: Headers including content type and authorization.
        """
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-Origin': 'metagpt',
            'X-Origin-Type': 'integration',
        }

    def _handle_error(self, response: requests.Response, action: str) -> None:
        """Handle API errors.

        Args:
            response (requests.Response): The response from the API.
            action (str): Description of the action being performed.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        try:
            error_message = response.json().get('error', 'No error message provided.')
            error_details = response.json().get('details', 'No additional error details provided.')
        except:
            raise requests.exceptions.HTTPError(
                f'Failed to parse Firecrawl error response as JSON. Status code: {response.status_code}',
                response=response
            )

        message = f"Error during {action}: Status code {response.status_code}. {error_message} - {error_details}"
        raise requests.exceptions.HTTPError(message, response=response)

    def map_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Map a URL to discover all available links.

        Args:
            url (str): The URL to map.
            params (Optional[Dict[str, Any]]): Additional parameters for the mapping operation.

        Returns:
            Dict[str, Any]: A dictionary containing the mapped URLs and related information.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'url': url}
        if params:
            json_data.update(params)

        response = requests.post(
            f'{self.api_url}/v1/map',
            headers=headers,
            json=json_data,
            timeout=self.request_timeout
        )

        if response.status_code == 200:
            try:
                return response.json()
            except:
                raise Exception('Failed to parse Firecrawl response as JSON.')
        else:
            self._handle_error(response, 'map URL')

    def scrape_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Scrape content from a specific URL.

        Args:
            url (str): The URL to scrape.
            params (Optional[Dict[str, Any]]): Additional parameters for the scraping operation.

        Returns:
            Dict[str, Any]: A dictionary containing the scraped content and metadata.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'url': url}
        if params:
            json_data.update(params)

        response = requests.post(
            f'{self.api_url}/v1/scrape',
            headers=headers,
            json=json_data,
            timeout=self.request_timeout
        )

        if response.status_code == 200:
            try:
                return response.json()
            except:
                raise Exception('Failed to parse Firecrawl response as JSON.')
        else:
            self._handle_error(response, 'scrape URL')

    def search(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform a web search using Firecrawl.

        Args:
            query (str): The search query.
            params (Optional[Dict[str, Any]]): Additional parameters for the search operation.

        Returns:
            Dict[str, Any]: A dictionary containing search results and metadata.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'query': query}
        if params:
            json_data.update(params)

        response = requests.post(
            f'{self.api_url}/v1/search',
            headers=headers,
            json=json_data,
            timeout=self.request_timeout
        )

        if response.status_code == 200:
            try:
                return response.json()
            except:
                raise Exception('Failed to parse Firecrawl response as JSON.')
        else:
            self._handle_error(response, 'search')

    def crawl_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start a crawl job for a given URL.

        Args:
            url (str): The URL to crawl.
            params (Optional[Dict[str, Any]]): Additional parameters for the crawl operation.

        Returns:
            Dict[str, Any]: A dictionary containing the crawl results and metadata.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'url': url}
        if params:
            json_data.update(params)

        response = requests.post(
            f'{self.api_url}/v1/crawl',
            headers=headers,
            json=json_data,
            timeout=self.request_timeout
        )

        if response.status_code == 200:
            try:
                return response.json()
            except:
                raise Exception('Failed to parse Firecrawl response as JSON.')
        else:
            self._handle_error(response, 'start crawl job')

    def get_crawl_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a crawl job.

        Args:
            job_id (str): The ID of the crawl job.

        Returns:
            Dict[str, Any]: A dictionary containing the crawl job status and results.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        headers = self._prepare_headers()
        response = requests.get(
            f'{self.api_url}/v1/crawl/{job_id}',
            headers=headers,
            timeout=self.request_timeout
        )

        if response.status_code == 200:
            try:
                return response.json()
            except:
                raise Exception('Failed to parse Firecrawl response as JSON.')
        else:
            self._handle_error(response, 'check crawl status')

    def extract(self, urls: List[str], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract structured information from URLs.

        Args:
            urls (List[str]): List of URLs to extract information from.
            params (Optional[Dict[str, Any]]): Additional parameters for the extraction operation.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted information and metadata.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'urls': urls}
        if params:
            json_data.update(params)

        response = requests.post(
            f'{self.api_url}/v1/extract',
            headers=headers,
            json=json_data,
            timeout=self.request_timeout
        )

        if response.status_code == 200:
            try:
                return response.json()
            except:
                raise Exception('Failed to parse Firecrawl response as JSON.')
        else:
            self._handle_error(response, 'extract')

    def get_extract_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of an extract job.

        Args:
            job_id (str): The ID of the extract job.

        Returns:
            Dict[str, Any]: A dictionary containing the extract job status and results.

        Raises:
            requests.exceptions.HTTPError: If the API request fails.
        """
        headers = self._prepare_headers()
        response = requests.get(
            f'{self.api_url}/v1/extract/{job_id}',
            headers=headers,
            timeout=self.request_timeout
        )

        if response.status_code == 200:
            try:
                return response.json()
            except:
                raise Exception('Failed to parse Firecrawl response as JSON.')
        else:
            self._handle_error(response, 'check extract status') 