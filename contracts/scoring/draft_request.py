"""Cross-module contract for draft generation requests (AI-003).

This DTO bundles the extracted content and product config into a single
context object for the draft generator. Consumed by PIPE-001 (pipeline
stage 5) when passing data to ``draft_reply()``.
"""

from pydantic import BaseModel

from contracts.config.product_config import ProductConfig
from contracts.extraction.extracted_content import ExtractedContent


class DraftContext(BaseModel):
    """Context bundle for the Sonnet draft generator.

    Combines the extracted page content with the product configuration
    so callers can pass a single object to ``draft_reply()``.

    Attributes:
        content: Extracted page content (title, body, existing comments).
        config: Product configuration (tone, pitch, mention, product_url).
    """

    content: ExtractedContent
    config: ProductConfig
