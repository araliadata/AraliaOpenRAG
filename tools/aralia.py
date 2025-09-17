"""Aralia Data Planet client and tools."""

import requests
import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional
from pydantic import Field, BaseModel

from utils.decorators import retry_on_failure
from utils.logging import get_logger

try:
    from langchain.tools import BaseTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Fallback base class
    class BaseTool(BaseModel):
        name: str
        description: str


class AraliaClient:
    """Client for interacting with Aralia Data Planet API.
    
    This class handles authentication, API calls, and data processing
    for Aralia Data Planet services.
    """
    
    def __init__(
        self,
        sso_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        stellar_url: Optional[str] = None
    ):
        """Initialize Aralia client.
        
        Args:
            sso_url: SSO service URL
            client_id: OAuth client ID
            client_secret: OAuth client secret
            stellar_url: Stellar API base URL
        """
        self.sso_url = sso_url or "https://sso.araliadata.io"
        self.client_id = client_id
        self.client_secret = client_secret
        self.stellar_url = stellar_url or "https://tw-air.araliadata.io"
        
        self.logger = get_logger("aralia_client")
        self.token: Optional[str] = None
        
        # Authenticate on initialization
        if client_id and client_secret:
            self.token = self._authenticate()
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _authenticate(self) -> str:
        """Authenticate with Aralia SSO service.
        
        Returns:
            Access token
            
        Raises:
            requests.RequestException: If authentication fails
        """
        self.logger.info("Authenticating with Aralia SSO")
        
        response = requests.post(
            f"{self.sso_url.rstrip('/')}/realms/stellar/protocol/openid-connect/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            },
            timeout=30
        )
        response.raise_for_status()
        
        token = response.json()["access_token"]
        self.logger.info("Successfully authenticated with Aralia SSO")
        return token
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Aralia API.
        
        Args:
            method: HTTP method (GET, POST)
            url: Request URL
            params: Query parameters for GET requests
            json_data: JSON payload for POST requests
            
        Returns:
            Response data
            
        Raises:
            requests.RequestException: If request fails
        """
        if not self.token:
            raise ValueError("Not authenticated. Please provide valid credentials.")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Try request, re-authenticate once if it fails
        for attempt in range(2):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                elif method.upper() == "POST":
                    response = requests.post(url, headers=headers, json=json_data, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                if response.status_code == 200:
                    break
                elif response.status_code == 401 and attempt == 0:
                    # Token might be expired, try to re-authenticate
                    self.logger.warning("Token expired, re-authenticating")
                    self.token = self._authenticate()
                    headers["Authorization"] = f"Bearer {self.token}"
                    continue
                else:
                    response.raise_for_status()
                    
            except requests.RequestException as e:
                if attempt == 0:
                    self.logger.warning(f"Request failed, retrying: {str(e)}")
                    continue
                raise
        
        data = response.json().get("data", {})
        return data.get("list", data)
    
    def search_datasets(self, question: str, page_size: int = 50) -> List[Dict[str, Any]]:
        """Search for datasets matching the given question.
        
        Args:
            question: Search query
            page_size: Maximum number of results to return
            
        Returns:
            List of matching datasets
        """
        self.logger.info(f"Searching datasets for: {question}")
        
        response = self._make_request(
            "GET",
            f"{self.stellar_url}/api/galaxy/dataset",
            params={
                "keyword": question,
                "pageSize": page_size
            }
        )
        
        # Process response to clean up URLs and remove unnecessary fields
        for item in response:
            if "sourceType" in item:
                item.pop("sourceType")
            if "sourceURL" in item:
                item['sourceURL'], _, _ = item['sourceURL'].partition('/admin')
        
        self.logger.info(f"Found {len(response)} datasets")
        return response
    
    def get_dataset_metadata(self, dataset_id: str, source_url: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific dataset.
        
        Args:
            dataset_id: Dataset identifier
            source_url: Source URL for the dataset
            
        Returns:
            Dataset metadata or None if not found
        """
        self.logger.info(f"Fetching metadata for dataset: {dataset_id}")
        
        try:
            metadata = self._make_request(
                "GET",
                f"{source_url}/api/dataset/{dataset_id}"
            )
            
            if not metadata:
                return None
            
            # Process columns
            cols_exclude = ["id", "name", "datasetID", "visible", "ordinalPosition", "sortingSettingID"]
            
            processed_columns = {}
            for column in metadata.get("columns", []):
                if column["type"] != "undefined" and column.get("visible", True):
                    processed_columns[column['id']] = {
                        "columnID": column["id"],
                        **{k: v for k, v in column.items() if k not in cols_exclude}
                    }
            
            # Get virtual variables if available
            try:
                virtual_vars = self._make_request(
                    "GET",
                    f"{source_url}/api/dataset/{dataset_id}/virtual-variables"
                )
                
                if virtual_vars:
                    virtual_exclude = ["id", "name", "datasetID", "visible", "setting", "sourceType", "language", "country"]
                    for var in virtual_vars:
                        processed_columns[var['id']] = {
                            "columnID": var["id"],
                            **{k: v for k, v in var.items() if k not in virtual_exclude}
                        }
            except Exception as e:
                self.logger.warning(f"Could not fetch virtual variables: {str(e)}")
            
            return {
                **metadata,
                "columns": processed_columns
            }
            
        except Exception as e:
            self.logger.error(f"Failed to fetch metadata for {dataset_id}: {str(e)}")
            return None
    
    def get_filter_options(self, dataset_id: str, source_url: str, filter_columns: List[Dict[str, Any]]) -> None:
        """Get filter options for specified columns.
        
        Args:
            dataset_id: Dataset identifier
            source_url: Source URL for the dataset
            filter_columns: List of column configurations to get filters for
        """
        self.logger.info(f"Fetching filter options for dataset: {dataset_id}")
        
        for filter_column in filter_columns:
            try:
                response = self._make_request(
                    "POST",
                    f"{source_url}/api/exploration/{dataset_id}/filter-options?start=0&pageSize=1000",
                    json_data={"x": [filter_column]}
                )
                
                filter_column['values'] = [item['x'][0][0] for item in response]
                
            except Exception as e:
                self.logger.error(f"Failed to get filter options for column {filter_column.get('columnID', 'unknown')}: {str(e)}")
                filter_column['values'] = []
    
    def execute_exploration(self, exploration_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute data exploration query.
        
        Args:
            exploration_config: Exploration configuration
            
        Returns:
            Query results
        """
        dataset_id = exploration_config['id']
        source_url = exploration_config['sourceURL']
        
        self.logger.info(f"Executing exploration for dataset: {dataset_id}")
        
        try:
            response = self._make_request(
                "POST",
                f"{source_url}/api/exploration/{dataset_id}?start=0&pageSize=1000",
                json_data=exploration_config
            )
            
            self.logger.info(f"Exploration returned {len(response)} results")
            return response
            
        except Exception as e:
            self.logger.error(f"Exploration failed for {dataset_id}: {str(e)}")
            return []


class AraliaSearchTool(BaseTool):
    """LangChain tool for searching Aralia datasets."""
    
    name: str = "aralia_dataset_search"
    description: str = (
        "Search for relevant datasets in Aralia Data Planet. "
        "Input should be a search query describing the type of data needed."
    )
    
    aralia_client: AraliaClient = Field(exclude=True)
    
    def _run(self, query: str) -> List[Dict[str, Any]]:
        """Execute the search.
        
        Args:
            query: Search query
            
        Returns:
            List of matching datasets
        """
        return self.aralia_client.search_datasets(query)
    
    async def _arun(self, query: str) -> List[Dict[str, Any]]:
        """Async execute the search.
        
        Args:
            query: Search query
            
        Returns:
            List of matching datasets
        """
        # For now, just call the sync version
        return self._run(query)
