import asyncio
from instantdomains.client import InstantDomainsClient

async def main():
    """
    An example of how to use the InstantDomainsClient.
    """
    client = InstantDomainsClient()
    try:
        # It's important to run the warmup sequence to initialize the session
        await client.warmup()
        
        domain_to_check = "dealerflow"
        search_results = await client.domain_search.search(domain_to_check)
        
        print(f"Results for '{search_results.query}':")
        
        print("\n--- Main TLDs ---")
        for result in search_results.main_results:
            status = "Available" if result.is_available else "Taken"
            print(f"{result.domain}: {status}")

        print("\n--- Suggested Domains ---")
        for result in search_results.suggested_results:
            status = "Available" if result.is_available else "Taken"
            print(f"{result.domain}: {status}")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())