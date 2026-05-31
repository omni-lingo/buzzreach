"""Cross-module contract for search queries (DISC-001).

Boundary between query construction (DISC-001) and the search client
(DISC-002). Consumed by DISC-003 to pass queries to the search client.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchQuery:
    """A single Google search query with freshness parameters.

    Attributes:
        query_text: The full search string (may include site: operators).
        tbs_param: Google time-based search param, e.g. ``qdr:h``, ``qdr:d``.
        source_hint: Optional hint about the intended source, e.g. ``reddit``.
    """

    query_text: str
    tbs_param: str
    source_hint: str = ""
