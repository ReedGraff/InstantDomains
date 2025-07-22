# InstantDomains SDK
[![PyPI version](https://badge.fury.io/py/instantdomains.svg)](https://badge.fury.io/py/instantdomains)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An unofficial, asynchronous Python SDK for reverse-engineered endpoints of `instantdomainsearch.com`.

## Overview

This SDK provides a simple, asynchronous client to programmatically check domain availability and get suggestions from InstantDomainSearch. It handles session initialization, cookie management, and parsing of various API responses into clean, consistent Pydantic models.

## Key Features

-   **Asynchronous:** Built with `httpx` and `asyncio` for non-blocking I/O.
-   **Session Management:** Automatically handles session warmup and cookies to mimic a real browser session.
-   **Structured Output:** Converts complex JSON responses into easy-to-use Pydantic models.
-   **Modular Design:** Endpoints are organized into logical API modules (e.g., `domain_search`).
-   **Dynamic Parsing:** Includes functions to parse different API responses into a unified format.

## Installation

To get started, install the pip package from PyPI:

```bash
pip install instantdomains
```

## How It Works

1.  **`InstantDomainsClient`**: The central entry point for the SDK. It manages the `httpx.AsyncClient` instance, base URLs, and headers.
2.  **`client.warmup()`**: A crucial first step. This method makes initial requests to the website to acquire necessary session cookies, which are required for subsequent API calls.
3.  **API Modules**: Functionality is divided into modules located in `instantdomains/api/`. For example, all domain searching logic is contained within the `DomainSearchAPI` class, accessible via `client.domain_search`.
4.  **Pydantic Models**: Each API module defines Pydantic models for its responses. The SDK ensures that no matter the structure of the raw data (HTML, JSON, etc.), the final output is always a validated and typed Pydantic object.

## Quick Example

Here is a basic example of how to use the client to search for a domain's availability across several TLDs.

```python
# InstantDomains/examples/0/runner.py
import asyncio
from instantdomains.client import InstantDomainsClient

async def main():
    """
    An example of how to use the InstantDomainsClient.
    """
    # Initialize the client
    client = InstantDomainsClient()
    try:
        # It's important to run the warmup sequence to initialize the session
        await client.warmup()
        
        domain_to_check = "dealerflow"
        # Define the TLDs you want to check
        tlds_to_check = {"com", "net", "ai", "io"}
        
        # Perform the search
        search_results = await client.domain_search.search(
            domain_name=domain_to_check, 
            tlds=tlds_to_check,
            get_suggestions=True
        )
        
        print(f"Results for '{search_results.query}':")
        
        print("\n--- Main TLDs ---")
        for result in search_results.main_results:
            status = "Available" if result.is_available else "Taken"
            print(f"{result.domain}: {status}")

        if search_results.suggested_results:
            print("\n--- Suggested Domains ---")
            for result in search_results.suggested_results:
                status = "Available" if result.is_available else "Taken"
                print(f"{result.domain}: {status}")

    finally:
        # Gracefully close the client session
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())

```

## Project Structure

The project is organized to separate concerns, with a clear distinction between the client, API logic, and data models.

```
instantdomains/
├── __init__.py
├── client.py                      # Holds the main InstantDomainsClient, session, and request logic
├── api/
│   ├── __init__.py
│   └── domain_search/
│       ├── index.py               # DomainSearchAPI class with search logic
│       └── models.py              # Pydantic models for domain search results
└── ...

examples/
└── 0/
    └── runner.py                  # Example usage script

README.md                          # This file
requirements.txt                   # Project dependencies
```

## Core Components

### `client.py`

This file contains the `InstantDomainsClient` class, which is the heart of the SDK. It is responsible for:
-   Managing the `httpx.AsyncClient` session.
-   Storing base URLs and common headers.
-   Handling the session `warmup()` flow for authentication.
-   A private `_request` method that centralizes error handling, logging, and execution of all HTTP requests.
-   Providing access to the various API modules (e.g., `self.domain_search`).

### `api/domain_search/`

This module encapsulates all functionality related to domain searches.
-   **`index.py`**: Defines the `DomainSearchAPI` class. It contains methods like `search()` which orchestrate calls to multiple endpoints, calculate required hashes, and use the parsing functions to process results.
-   **`models.py`**: Defines the Pydantic models (`DomainInfo`, `DomainSearchResults`) that provide the structured output for the search results. This ensures that the user of the SDK always receives a predictable and easy-to-work-with object.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Contributing

Contributions are welcome! Please leave issues or pull requests on the GitHub repository.