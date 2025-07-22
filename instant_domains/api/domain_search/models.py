from pydantic import BaseModel, Field
from typing import List, Optional

class DomainInfo(BaseModel):
    """
    Pydantic model representing the status of a single domain.
    """
    domain: str
    is_available: bool

class DomainSearchResults(BaseModel):
    """
    Pydantic model for holding all domain search results.
    """
    query: str
    main_results: List[DomainInfo] = Field(default_factory=list)
    suggested_results: List[DomainInfo] = Field(default_factory=list)