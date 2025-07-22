import asyncio
import os
import json
import logging
import csv
from typing import List, Set, Dict, Any
from dotenv import load_dotenv
import openai
from pydantic import Field

# Local project imports
from instant_domains.client import InstantDomainsClient
from schemic import SchemicModel

# --- Logger Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- AI Integration Setup ---

# Load environment variables from a .env file
load_dotenv()

# Initialize the OpenAI client, handling potential missing API key
try:
    openai_client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
except KeyError:
    logger.error("FATAL: The 'OPENAI_API_KEY' environment variable is not set.")
    logger.error("Please create a .env file and add the key, then restart the script.")
    exit()

# --- Schemic Models for Structured AI Output ---

class DomainNameIdeas(SchemicModel):
    """A model to hold a list of generated domain name ideas from the AI."""
    ideas: List[str] = Field(
        ..., 
        description="A list of creative and brandable domain name ideas. These should be single words without the TLD (e.g., 'zenith', 'brightwork', 'catalyst')."
    )

# --- Functions for AI Interaction ---

def get_domain_ideas(prompt: str, num_ideas: int = 15) -> List[str]:
    """
    Uses GPT to generate a list of startup domain name ideas based on a user prompt.

    Args:
        prompt (str): The user's startup idea description.
        num_ideas (int): The number of ideas to generate.

    Returns:
        List[str]: A list of domain name ideas (without TLDs).
    """
    logger.info(f"\nAsking AI for startup name ideas for: '{prompt}'...")
    try:
        response = openai_client.chat.completions.create(
            model="o4-mini-2025-04-16",
            messages=[
                {"role": "system", "content": """You are an expert in branding and naming startups. Generate a diverse list of short, memorable, and unique names based on the user's idea.

To generate ideas, use the following techniques:
0.  Exhaust all combinations of key terms in the description. Try using the terms most specific to the startup's industry. So for a company working in the logistics space, you might get 'LogisticsPro', 'CargoFlow', 'ShipSmart', 'FreightWise', etc. Not something like 'Fixify' or 'SuperFixer' or 'ServiceX'. Also adding the most common terms in the industry so for something in the car dealership space you might want to include terms like 'auto'.
1.  Only when you have exhausted the key terms in the description, use these tools to find additional domains:
    * Synonyms and related concepts for the core idea (e.g., for 'auto parts', think 'parts', 'tools', for 'construction' think 'building', 'builders', 'contractors' But only if the synonym is relevant within the context of the rest of the description).
    * Appending or prepending common branding modifiers like 'er', 'r', 'x', 'ing', 'y', 'ly', 'ify', 'flow', 'wise', 'hub'.
    * Using prefixes like 'try', 'get', 'go', 'we', 'wedo'.
    * Reversing words (so for a company doing 'permit's, you might get 'timrep').
2.  Combine keywords in interesting ways (e.g., 'PartPilot', 'OrderFlow').
3.  Avoid using generic terms like 'tech', 'solutions', 'systems', 'AI', 'assistant', & 'bot' unless they are part of the core idea.
4.  Avoid using special characters like '-', '_'.
5.  Avoid misspellings or overly complex names that are hard to remember or spell (including in most cases, the use of numbers, or removing all vowels in a name).
"""},
                {"role": "user", "content": f"My startup idea is: {prompt}. Please give me a list of {num_ideas} potential names."}
            ],
            response_format=DomainNameIdeas.schemic_schema(),
        )
        content = response.choices[0].message.content
        if content:
            parsed_response = DomainNameIdeas(**json.loads(content))
            logger.info(f"AI generated {len(parsed_response.ideas)} ideas.")
            return parsed_response.ideas
    except Exception:
        logger.exception("Error getting domain ideas from AI.")
    return []

# --- Main Application Logic ---

async def main(startup_idea: str, allowed_tlds: Set[str], only_show_available: bool, get_suggestions: bool, num_ideas: int):
    """
    Main runner to find, filter, and sort startup domain names using AI and the InstantDomainsSDK.
    
    Args:
        startup_idea (str): A description of the startup.
        allowed_tlds (Set[str]): A set of allowed TLDs to filter for (e.g., {'.com', '.io'}).
        only_show_available (bool): If True, only saves available domains to the CSV.
        get_suggestions (bool): If True, fetches additional domain suggestions from InstantDomains.
        num_ideas (int): The number of domain ideas to request from the AI.
    """
    logger.info("--- Startup Domain Name Finder ---")

    # 1. Get initial ideas from AI
    ideas_from_gpt = get_domain_ideas(startup_idea, num_ideas=num_ideas)
    if not ideas_from_gpt:
        logger.error("Could not generate initial ideas. Exiting.")
        return

    # 2. Check domain availability using the SDK
    client = InstantDomainsClient()
    all_results_data: Dict[str, Dict[str, Any]] = {}

    try:
        await client.warmup()
        logger.info(f"\nChecking availability for {len(ideas_from_gpt)} names and suggestions...")

        # Create concurrent tasks for all domain searches
        tasks = [client.domain_search.search(idea, allowed_tlds, get_suggestions=get_suggestions) for idea in ideas_from_gpt]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Error during domain search: {res}", exc_info=False)
                continue

            # Process main results (from AI idea + common TLDs)
            for domain_info in res.main_results:
                if any(domain_info.domain.endswith(tld) for tld in allowed_tlds):
                    all_results_data[domain_info.domain] = {
                        "source": "AI-Generated",
                        "available": domain_info.is_available
                    }
            
            # Process suggested results (from InstantDomains)
            for domain_info in res.suggested_results:
                if any(domain_info.domain.endswith(tld) for tld in allowed_tlds):
                    # Avoid overwriting if already present from main results
                    if domain_info.domain not in all_results_data:
                         all_results_data[domain_info.domain] = {
                            "source": "InstantDomains Suggestion",
                            "available": domain_info.is_available
                        }
        
        tld_str = ", ".join(allowed_tlds)
        logger.info(f"Checked {len(all_results_data)} total domains ending in {tld_str}.")

    finally:
        await client.close()
    
    if not all_results_data:
        logger.info("\nNo domains found. Try a different prompt.")
        return

    # 3. Write results to CSV
    output_filename = "domain_results.csv"
    logger.info(f"\nWriting results to {output_filename}...")
    
    # Prepare data for CSV
    final_data = []
    for domain, data in all_results_data.items():
        if only_show_available and not data["available"]:
            continue
        final_data.append({
            "Domain": domain,
            "Source": data["source"],
            "Status": "Available" if data["available"] else "Not Available"
        })

    # Sort alphabetically by domain name
    final_data.sort(key=lambda x: x["Domain"])

    if not final_data:
        logger.info("No domains matched the specified criteria (e.g., only available).")
        return

    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Domain", "Source", "Status"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_data)
        logger.info(f"Successfully saved {len(final_data)} domains to {output_filename}.")
    except IOError:
        logger.exception(f"Error writing to file {output_filename}.")


if __name__ == "__main__":
    # --- Configuration ---
    STARTUP_IDEA = "An AI parts assistant for car dealerships. It helps the parts desk manage inventory and automatically builds repair orders from service line descriptions."
    ALLOWED_TLDS = {'com', 'ai'} # , 'io', 'net', 'org'
    # Set to True to only get available domains, False to get all results.
    ONLY_SHOW_AVAILABLE = False
    # Set to True to get additional suggestions from InstantDomains, False to only check AI-generated names.
    GET_SUGGESTIONS = False
    # The number of domain ideas to request from the AI.
    NUM_IDEAS = 300

    try:
        asyncio.run(main(
            startup_idea=STARTUP_IDEA, 
            allowed_tlds=ALLOWED_TLDS, 
            only_show_available=ONLY_SHOW_AVAILABLE,
            get_suggestions=GET_SUGGESTIONS,
            num_ideas=NUM_IDEAS
        ))
    except KeyboardInterrupt:
        logger.info("\nScript interrupted. Exiting.")
    except Exception:
        logger.exception("An unexpected error occurred during script execution.")
