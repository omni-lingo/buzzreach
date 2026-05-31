"""Tech niche bundles (QUALITY-004).

SaaS, Tech Support, Education.
"""

from src.backend.services.quality.seed_bundles import SeedBundle, _tpl

TECH_BUNDLES: list[SeedBundle] = [
    SeedBundle(
        name="SaaS & Software",
        slug="saas",
        description=(
            "Reach people comparing software tools "
            "and looking for alternatives."
        ),
        keywords=[
            "alternative to", "which tool for",
            "best app for", "software recommendation",
            "SaaS comparison",
        ],
        platforms=[
            "Reddit r/SaaS", "Product Hunt",
            "Reddit r/startups", "Reddit r/Entrepreneur",
        ],
        tone="friendly",
        tone_description=(
            "Conversational and helpful. Focus on features "
            "and use cases. Be honest about pros/cons."
        ),
        templates=[
            _tpl(
                "SaaS Alternative", "casual",
                "Suggest as an alternative tool",
                "I've tried several options and "
                "{product_name} has been the best fit.\n\n"
                "What stood out:\n"
                "- {feature_1}\n- {feature_2}\n\n"
                "Check it out: {product_url}",
            ),
            _tpl(
                "SaaS Comparison", "professional",
                "Compare tools objectively",
                "I've used both and here's my take:\n\n"
                "**{competitor}:** {competitor_pros}\n"
                "**{product_name}:** {product_pros}\n\n"
                "For {use_case}, {product_name} won "
                "because {key_benefit}.\n\n"
                "Details: {product_url}",
            ),
            _tpl(
                "SaaS Feature Highlight", "technical",
                "Highlight a specific feature",
                "Great question! {product_name} handles "
                "this well.\n\n{product_description}\n\n"
                "Key feature: {key_benefit}.\n\n"
                "More info: {product_url}",
            ),
        ],
        icon="cloud",
    ),
    SeedBundle(
        name="Tech Support",
        slug="tech-support",
        description=(
            "Help people with technical problems. "
            "Clear, step-by-step tone."
        ),
        keywords=[
            "error", "not working", "how to fix",
            "troubleshoot", "bug report",
        ],
        platforms=[
            "Stack Overflow", "Reddit r/techsupport",
            "Reddit r/sysadmin", "Reddit r/webdev",
        ],
        tone="technical",
        tone_description=(
            "Clear, precise, and helpful. Use code examples "
            "when appropriate. Solve the problem."
        ),
        templates=[
            _tpl(
                "Technical Fix", "technical",
                "Provide a technical solution",
                "I've dealt with this exact issue.\n\n"
                "The fix: {suggestion_1}\n\n"
                "If that doesn't work, try "
                "{suggestion_2}.\n\n"
                "{product_name} automates this: "
                "{product_url}",
            ),
            _tpl(
                "Step-by-Step Debug", "technical",
                "Walk through debugging steps",
                "Here's how to debug this:\n\n"
                "1. {step_1}\n2. {step_2}\n"
                "3. {step_3}\n\n"
                "For monitoring, {product_name} "
                "handles this well: {product_url}",
            ),
        ],
        icon="wrench",
    ),
    SeedBundle(
        name="Education & Learning",
        slug="education",
        description=(
            "Reach students and learners looking for "
            "courses and study materials."
        ),
        keywords=[
            "best course for", "learn how to",
            "study resources", "online class",
            "tutorial recommendation",
        ],
        platforms=[
            "Reddit r/learnprogramming",
            "Reddit r/OnlineLearning",
            "Quora", "Reddit r/college",
        ],
        tone="friendly",
        tone_description=(
            "Encouraging and patient. Share learning "
            "paths and personal experience."
        ),
        templates=[
            _tpl(
                "Learning Resource", "casual",
                "Recommend a learning resource",
                "I learned this the same way!\n\n"
                "What worked: {suggestion_1}. "
                "{product_name} is great because "
                "{product_description}.\n\n"
                "Start here: {product_url}",
            ),
            _tpl(
                "Study Path", "technical",
                "Outline a study path",
                "Here's a study path that worked:\n\n"
                "1. {step_1}\n2. {step_2}\n"
                "3. {step_3}\n\n"
                "{product_name} covers all of this: "
                "{product_url}",
            ),
        ],
        icon="book",
    ),
]
