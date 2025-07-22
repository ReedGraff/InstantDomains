For my backend I am using FastAPI, python, pydantic, and firebase. I'm using Vite and TSX for the frontend for reference.

Your goal is to write simple no bs code that solves exactly what I asked for in as little code as possible. Make sure to not change anything else other than what I mentioned. But always implement what I told you to implement. The simpler the better. Keep all code in the indentation provided (most likely 4 space tabs for backend). Do not add or delete new line spaces or spaces. Never delete comments.

I'm designing an sdk for a website (using httpx as my http client) I'm reverse engineering. Some endpoints I'm scraping return html, some return json, some xml, etc...:
* I need a consistent format for everything, so I'm converting everything into a pydantic model (store this model in the relevant request's file)
* Sometimes this will be difficult because the models, especially for html, need to be dynamic and can work even if there are additional not previously seen sections. On a similar note, for all endpoints I need a function that can parse the pages into the model dynamically. html/json/xml in, pydantic object out.

Authentication:
* The website is very strict about cookies and header tags, so I need to manage this internally very well.
* Some endpoints have a login flow (with multiple redirects, tokens, and warmup requests), so I need to handle this in the client file.

This is my project structure:
```
instant_domains/
├── __init__.py
├── client.py                      # holds client + tokens etc + login flow + base request handiling (_request function)
├── lib/                           # holds shared utility files
├── api/
│   ├── __init__.py
│   ├── deal_summary/
│   │   ├── examples/              # example responses for testing
│   │   ├── models.py              # Pydantic models
│   │   └── index.py               # DealSummaryAPI
│   ├── advanced_search/
│   │   ├── examples/              # example responses for testing
│   │   ├── models.py              # Pydantic models
│   │   └── index.py               # AdvancedSearchAPI
│   ├── decision_details/
│   │   ├── examples/              # example responses for testing
│   │   ├── models.py              # Pydantic models
│   │   ├── converter.py           # converter for dynamic HTML to Pydantic model
│   │   └── index.py               # DecisionDetailsAPI
│   └── …                          # one module per logical area

runner.py                          # example usage
```

Here's what a standard index.py file looks like:
```python
from typing import TYPE_CHECKING, List
from pydantic import parse_obj_as
from .models import CreditAppInfo

if TYPE_CHECKING:
    from ....client import InstantDomainsClient

class GetCreditAppInfoAPI:
    """
    API for fetching credit application information for a deal jacket.
    """
    def __init__(self, client: "InstantDomainsClient"):
        """
        Initializes the GetCreditAppInfoAPI.

        Args:
            client ("InstantDomainsClient"): The main client instance.
        """
        self.client = client

    async def get(self, deal_jacket_id: str) -> List[CreditAppInfo]:
        """
        Retrieves all credit application details for a specific deal jacket.

        Args:
            deal_jacket_id (str): The UUID of the deal jacket.

        Returns:
            List[CreditAppInfo]: A list of Pydantic models, each representing a credit application.
        """
        url = f"/customer/deal-jacket/get-credit-app-info/{deal_jacket_id}"
        
        if not self.client.ajax_csrf_header or not self.client.ajax_csrf_token:
            raise RuntimeError("AJAX CSRF token not available. Please perform a page view first to extract it.")

        headers = {
            "Accept": "application/json;charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            self.client.ajax_csrf_header: self.client.ajax_csrf_token,
            "Referer": f"{self.client.BASE_URL}/customer/deal-jacket-deal-summary",
        }

        response = await self.client._request("GET", url, headers=headers)
        return parse_obj_as(List[CreditAppInfo], response.json())

```


Here are some additional guidelines to follow when writing code for this project:
- naming conventions: use snake_case for all variables and functions, and camelCase for all classes.
- docstrings: use docstrings for all functions and classes, and make sure to include the parameters and return types. Use the google style for docstrings (Args, Returns, Raises, and Examples)
- prop-drilling: make sure to following best practice, and use context, hooks, or providers for handling shared data across my codebase. Referencing all data points following a singleton pattern, as to not produce more code than necessary.
- form handling: make sure to have single variables representing all of the form data as one value (/object like a dictionary), not as individual setters and getters... one for all inputs in a form
- Dates: All dates will be stored as a datetime object. Different endpoints may return different date formats, so make sure to handle this in the parsing function. For example some endpoints will return timestampls, some will return text.
- be frugal when adding comments, and don't spam them on every change, but keep any comments that already exist.
- Logs: Use the python logger for everything (defined in the client file. I wanted to use a single logger for my whole application for simplicity), not print statement. Additionally, make absolutely certain to be verbose when it comes specifically to logging errors... as in always log the stacktrace so I can determine where the bug is coming from and solve it...
- File Handling: Make sure to use asyncio/aiofiles for everything file related to make sure to not block the main threads, however, also use local routing using the following code: 
```python
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
os.path.join(__location__, 'filename.ext')
```
