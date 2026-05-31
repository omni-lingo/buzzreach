"""Global seed template definitions for BuzzReach (QUALITY-003).

Contains the default templates shipped with every BuzzReach instance.
Each template includes placeholder variables like {product_name} and
{user_name} that are auto-filled from user settings when applied.

Cross-module contracts:
- Consumed by TemplateService.seed_global_templates()
- None — leaf module (seed data only).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SeedTemplate:
    """Definition of a global template to be seeded."""

    name: str
    category: str
    description: str
    text: str


GLOBAL_TEMPLATES: list[SeedTemplate] = [
    SeedTemplate(
        name="Technical Support",
        category="technical",
        description="For programming and technical help threads",
        text=(
            "Great question! I've worked with this exact issue before.\n\n"
            "{product_name} handles this by {product_description}. "
            "You can check it out at {product_url}.\n\n"
            "Here's what I'd suggest:\n"
            "1. First, try {suggestion_1}\n"
            "2. If that doesn't work, {suggestion_2}\n\n"
            "Hope this helps! Happy to answer follow-ups."
        ),
    ),
    SeedTemplate(
        name="Legal Advice",
        category="professional",
        description="For legal question threads requiring careful tone",
        text=(
            "I'm not a lawyer, but I can share some perspective on "
            "this.\n\n"
            "Based on my experience with {product_name}, "
            "{product_description}. You might want to look into "
            "{suggestion_1}.\n\n"
            "That said, I'd recommend consulting a professional for "
            "your specific situation. {product_url} has some resources "
            "that might be helpful."
        ),
    ),
    SeedTemplate(
        name="Product Recommendation",
        category="persuasive",
        description="For product comparison and recommendation threads",
        text=(
            "I've tried several options and {product_name} has been "
            "the best fit for me.\n\n"
            "What stood out:\n"
            "- {feature_1}\n"
            "- {feature_2}\n"
            "- {feature_3}\n\n"
            "You can see it in action at {product_url}. "
            "Let me know if you have any questions about it!"
        ),
    ),
    SeedTemplate(
        name="Experience Share",
        category="casual",
        description="For story-based questions and personal experience",
        text=(
            "I went through something similar! Here's what worked "
            "for me.\n\n"
            "I started using {product_name} about {timeframe} ago "
            "when I was dealing with {problem}. "
            "{product_description}\n\n"
            "The biggest win for me was {key_benefit}. Check it out: "
            "{product_url}"
        ),
    ),
    SeedTemplate(
        name="How-To Guide",
        category="technical",
        description="Step-by-step instructions for how-to questions",
        text=(
            "Here's a step-by-step approach:\n\n"
            "1. {step_1}\n"
            "2. {step_2}\n"
            "3. {step_3}\n\n"
            "If you want to automate this, {product_name} does "
            "exactly that: {product_description}.\n\n"
            "Full details at {product_url}."
        ),
    ),
    SeedTemplate(
        name="Community Helper",
        category="empathetic",
        description="Empathetic response for frustrated or stuck users",
        text=(
            "I totally understand the frustration — I've been there "
            "too.\n\n"
            "{user_name}, what helped me was {suggestion_1}. "
            "Also, {product_name} made a big difference because "
            "{product_description}.\n\n"
            "Feel free to DM me if you want more details. "
            "Here's the link: {product_url}"
        ),
    ),
    SeedTemplate(
        name="Reddit Quick Reply",
        category="reddit",
        description="Short, conversational Reddit reply format",
        text=(
            "This is actually a common question on this sub.\n\n"
            "Short answer: {short_answer}\n\n"
            "Longer version: {product_name} handles this well — "
            "{product_description}. Link: {product_url}"
        ),
    ),
    SeedTemplate(
        name="Quora Detailed Answer",
        category="quora",
        description="Structured Quora answer with authority",
        text=(
            "Having worked in this space for a while, I can share "
            "some insights.\n\n"
            "**The Problem:** {problem}\n\n"
            "**The Solution:** {product_name} addresses this by "
            "{product_description}.\n\n"
            "**Why it works:** {key_benefit}\n\n"
            "More info: {product_url}"
        ),
    ),
    SeedTemplate(
        name="Blog Comment",
        category="blog",
        description="Thoughtful blog comment adding value",
        text=(
            "Great article! This aligns with what I've seen using "
            "{product_name}.\n\n"
            "One thing I'd add: {suggestion_1}. "
            "{product_description}\n\n"
            "For anyone interested: {product_url}"
        ),
    ),
    SeedTemplate(
        name="Comparison Response",
        category="professional",
        description="Objective comparison response for versus threads",
        text=(
            "I've used both and here's my honest take:\n\n"
            "**{competitor}:** {competitor_pros}\n"
            "**{product_name}:** {product_pros}\n\n"
            "For my use case ({use_case}), {product_name} won "
            "because {key_benefit}.\n\n"
            "Details: {product_url}"
        ),
    ),
]
