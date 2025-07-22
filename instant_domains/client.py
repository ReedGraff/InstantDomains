import httpx
import logging
import traceback
from urllib.parse import urljoin

from .api.domain_search.index import DomainSearchAPI

# Setup logger
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstantDomainsClient:
    """
    The main client for interacting with the InstantDomains API.
    Handles session management and provides access to API endpoints.
    """
    BASE_URL = "https://instantdomainsearch.com"
    API_BASE_URL = "https://api.instantdomainsearch.com"

    def __init__(self):
        """
        Initializes the InstantDomainsClient.
        """
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Connection": "keep-alive",
            },
            follow_redirects=True,
            timeout=30.0,
        )

        # Initialize API modules
        self.domain_search = DomainSearchAPI(self)

    async def warmup(self):
        """
        Performs the warmup sequence to initialize the session and gather necessary cookies.
        """
        logger.info("Step 1: Warming up session...")
        # Initial page load to get cookies
        await self._request("GET", "/")
        logger.debug("Initial cookies set from main page.")
        
        # Geography service call
        geography_url = urljoin(self.API_BASE_URL, "/services/geography")
        await self._request("GET", geography_url, headers={"Referer": f"{self.BASE_URL}/"})
        
        # Auth session call
        auth_session_url = urljoin(self.API_BASE_URL, "/services/auth/session")
        await self._request("GET", auth_session_url, headers={"Referer": f"{self.BASE_URL}/"})

        logger.info("Session warmup complete.")

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Internal request handler with session and error management.

        Args:
            method (str): HTTP method (GET, POST, etc.).
            url (str): The URL for the request.
            **kwargs: Additional arguments for httpx.request.

        Returns:
            httpx.Response: The response object.
        """
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            # httpx automatically manages cookies, so we don't need to manually update them
            return response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error for {e.request.url}: {e.response.status_code} - {e.response.text}")
            logger.error(traceback.format_exc())
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during request to {url}: {e}")
            logger.error(traceback.format_exc())
            raise

    async def close(self):
        """
        Closes the httpx client session.
        """
        await self.client.aclose()
        logger.debug("HTTP client session closed.")