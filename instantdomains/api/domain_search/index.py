from typing import TYPE_CHECKING, List, Set
import ctypes
from .models import DomainInfo, DomainSearchResults

if TYPE_CHECKING:
    from ....client import InstantDomainsClient

class DomainSearchAPI:
    """
    API for searching domain availability and getting suggestions.
    """
    def __init__(self, client: "InstantDomainsClient"):
        """
        Initializes the DomainSearchAPI.

        Args:
            client ("InstantDomainsClient"): The main client instance.
        """
        self.client = client
        self.common_tlds = "com,net,org,ai,io,xyz,app,shop,info,co,store,site,online,dev,tech,pro,live,lol,club,vip,link,top,me,tv,blog,cloud,design,studio,art,fun,one,world,digital,global,space,plus,media,email,host,page,ltd,biz,agency,social,stream,zone,web,team,work,life,love,best,cool,today,guru,care,fit,marketing,luxury,solutions,services,money,consulting,bio"

    def _calculate_hash(self, s: str, seed: int = 0) -> str:
        """
        A Python implementation of the djb2-variant string hashing function.
        
        Args:
            s: The string to hash.
            seed: An optional seed value.
            
        Returns:
            The calculated hash as a string.
        """
        # Use ctypes.c_int32 to mimic JavaScript's 32-bit signed integer behavior
        hash_val = ctypes.c_int32(seed)
        
        for char in s:
            char_code = ord(char)
            # The core djb2-variant algorithm
            temp_hash = (hash_val.value << 5) - hash_val.value + char_code
            # Assigning back to .value truncates the result to a 32-bit signed integer
            hash_val.value = temp_hash
            
        return str(hash_val.value)

    def _parse_zone_results(self, json_data: dict) -> List[DomainInfo]:
        """
        Parses the JSON response from the /services/zone-names endpoint.

        Args:
            json_data (dict): The JSON data from the API response.

        Returns:
            List[DomainInfo]: A list of Pydantic models for each domain.
        """
        results = []
        for item in json_data.get("results", []):
            domain_name = f"{item.get('label', '')}.{item.get('tld', '')}"
            is_available = not item.get("isRegistered", True)
            results.append(DomainInfo(domain=domain_name, is_available=is_available))
        return results
    
    def _parse_verisign_results(self, json_data: dict) -> List[DomainInfo]:
        """
        Parses the JSON response from the /services/verisign/check endpoint.

        Args:
            json_data (dict): The JSON data from the API response.

        Returns:
            List[DomainInfo]: A list of Pydantic models for each domain.
        """
        results = []
        for item in json_data.get("data", {}).get("results", []):
            is_available = item.get("availability") == "available"
            results.append(DomainInfo(domain=item.get("name"), is_available=is_available))
        return results

    async def search(self, domain_name: str, tlds: Set[str], get_suggestions: bool = True) -> DomainSearchResults:
        """
        Retrieves the availability of a domain across multiple TLDs and gets suggestions.

        Args:
            domain_name (str): The domain name to search for (e.g., "example").
            tlds (Set[str]): A set of TLDs to search for (e.g., {".com", ".ai"}).
            get_suggestions (bool): Whether to fetch additional suggestions from InstantDomains.

        Returns:
            DomainSearchResults: A Pydantic model containing the search results.
        """
        label = domain_name.split('.')[0]
        # This hash is used for the zone-names and fix endpoints
        domain_hash = self._calculate_hash(label, 42)
        
        # Format TLDs for the API call (e.g., {".com", ".ai"} -> "com,ai")
        tlds_str = ",".join(tld.strip('.') for tld in tlds)

        # 1. Get main TLD variations
        zone_url = f"/services/zone-names/{label}?hash={domain_hash}&limit=64&city=Houston&country=US&tlds={tlds_str}"
        zone_response = await self.client._request("GET", zone_url)
        main_results = self._parse_zone_results(zone_response.json())
        
        suggested_results = []
        if get_suggestions:
            # 2. Get suggested domain names
            fix_url = f"/services/fix/{label}?hash={domain_hash}&limit=32&city=Houston&country=US&tlds={tlds_str}"
            fix_response = await self.client._request("GET", fix_url)
            suggestions = fix_response.json().get("results", [])
            suggested_names = [s.get("label") + "." + s.get("tld") for s in suggestions if s.get("label") and s.get("tld")]

            # 3. Bulk check availability of suggestions
            if suggested_names:
                verisign_url = "/services/verisign/check"
                # This hash must be calculated with a seed of 27 for the verisign check
                verisign_hash = self._calculate_hash(label, 27) 
                data = {
                    "hash": verisign_hash,
                    "names": ",".join(suggested_names),
                    "search": label,
                    "tlds": tlds_str
                }
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "*/*",
                    "Referer": f"{self.client.BASE_URL}/"
                }
                verisign_response = await self.client._request("POST", verisign_url, data=data, headers=headers)
                suggested_results = self._parse_verisign_results(verisign_response.json())

        return DomainSearchResults(
            query=domain_name,
            main_results=main_results,
            suggested_results=suggested_results,
        )
