"""Professional niche bundles (QUALITY-004).

Legal, Real Estate, Finance, Marketing.
"""

from src.backend.services.quality.seed_bundles import SeedBundle, _tpl

PROFESSIONAL_BUNDLES: list[SeedBundle] = [
    SeedBundle(
        name="Legal Services",
        slug="legal-services",
        description=(
            "Target people seeking legal advice. "
            "Professional tone with disclaimers."
        ),
        keywords=[
            "lawsuit advice", "legal help",
            "need a lawyer", "legal question", "court case",
        ],
        platforms=[
            "Reddit r/legaladvice", "Avvo", "Reddit r/law",
        ],
        tone="professional",
        tone_description=(
            "Authoritative but careful. Include disclaimers. "
            "Share resources, not advice."
        ),
        templates=[
            _tpl(
                "Legal Resource Share", "professional",
                "Share legal resources carefully",
                "I'm not a lawyer, but I can share perspective."
                "\n\nBased on experience with {product_name}, "
                "{product_description}. Look into "
                "{suggestion_1}.\n\nConsult a professional. "
                "{product_url} has resources.",
            ),
            _tpl(
                "Legal Process Guide", "professional",
                "Explain legal processes",
                "This is a common concern.\n\n"
                "1. {step_1}\n2. {step_2}\n3. {step_3}\n\n"
                "{product_name} can help: {product_url}",
            ),
        ],
        icon="scale",
    ),
    SeedBundle(
        name="Real Estate",
        slug="real-estate",
        description=(
            "Connect with home buyers, sellers, and renters "
            "seeking property advice."
        ),
        keywords=[
            "buying a house", "real estate agent",
            "property investment", "rent vs buy",
            "housing market",
        ],
        platforms=[
            "Reddit r/RealEstate",
            "Reddit r/FirstTimeHomeBuyer",
            "Zillow forums",
        ],
        tone="professional",
        tone_description=(
            "Knowledgeable and trustworthy. Use market data. "
            "Avoid overpromising returns."
        ),
        templates=[
            _tpl(
                "Real Estate Insight", "professional",
                "Share market insight",
                "Great question about the market.\n\n"
                "From what I've seen, {suggestion_1}. "
                "{product_name} provides "
                "{product_description}.\n\n"
                "Worth checking: {product_url}",
            ),
            _tpl(
                "Home Buying Guide", "professional",
                "Guide for first-time buyers",
                "As a first-time buyer:\n\n"
                "1. {step_1}\n2. {step_2}\n3. {step_3}\n\n"
                "{product_name} simplifies this: {product_url}",
            ),
        ],
        icon="home",
    ),
    SeedBundle(
        name="Personal Finance",
        slug="personal-finance",
        description=(
            "Engage with people managing money, budgeting, "
            "and seeking financial guidance."
        ),
        keywords=[
            "save money", "budget help",
            "investment advice", "debt payoff",
            "financial planning",
        ],
        platforms=[
            "Reddit r/personalfinance",
            "Reddit r/FinancialPlanning",
            "Reddit r/frugal",
        ],
        tone="professional",
        tone_description=(
            "Responsible and educational. Never guarantee "
            "returns. Focus on principles and tools."
        ),
        templates=[
            _tpl(
                "Finance Tip", "professional",
                "Share a money-saving approach",
                "I've been in a similar situation.\n\n"
                "What helped: {suggestion_1}. "
                "{product_name} made tracking easier "
                "because {product_description}.\n\n"
                "More info: {product_url}",
            ),
            _tpl(
                "Budgeting Guide", "empathetic",
                "Help with budgeting",
                "Budgeting doesn't have to be hard.\n\n"
                "Start with: {step_1}\nThen: {step_2}\n\n"
                "I use {product_name}: {product_url}",
            ),
        ],
        icon="wallet",
    ),
    SeedBundle(
        name="Marketing & Growth",
        slug="marketing",
        description=(
            "Reach marketers and business owners "
            "looking for growth strategies."
        ),
        keywords=[
            "marketing strategy", "grow my business",
            "social media tips", "SEO help",
            "content marketing",
        ],
        platforms=[
            "Reddit r/marketing",
            "Reddit r/digital_marketing",
            "Reddit r/SEO", "Indie Hackers",
        ],
        tone="professional",
        tone_description=(
            "Data-driven and practical. Share specific "
            "results and metrics. Avoid hype."
        ),
        templates=[
            _tpl(
                "Marketing Strategy", "professional",
                "Share a marketing approach",
                "I've tested this and it works.\n\n"
                "Key results: {feature_1}\n\n"
                "{product_name} made this possible: "
                "{product_description}.\n\n"
                "Details: {product_url}",
            ),
            _tpl(
                "Growth Hack", "casual",
                "Share a growth tactic",
                "A tactic that moved the needle:\n\n"
                "1. {step_1}\n2. {step_2}\n\n"
                "I use {product_name} to automate this: "
                "{product_url}",
            ),
        ],
        icon="megaphone",
    ),
]
