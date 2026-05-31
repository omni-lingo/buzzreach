"""Discovery service — search query construction and provider client."""

from src.backend.services.discovery.query_builder import build_queries
from src.backend.services.discovery.search_client import SearchClient

__all__ = ["SearchClient", "build_queries"]
