"""Lifestyle niche bundles (QUALITY-004).

E-commerce, Fitness, Food, Travel, Parenting.
"""

from src.backend.services.quality.seed_bundles import SeedBundle, _tpl

LIFESTYLE_BUNDLES: list[SeedBundle] = [
    SeedBundle(
        name="E-commerce",
        slug="ecommerce",
        description=(
            "Find shoppers seeking product "
            "recommendations and purchase advice."
        ),
        keywords=[
            "where to buy", "need recommendation",
            "best seller", "product review",
            "shopping advice",
        ],
        platforms=[
            "Reddit r/ecommerce",
            "Reddit r/BuyItForLife", "Reddit r/Deals",
        ],
        tone="friendly",
        tone_description=(
            "Warm and approachable. Focus on product "
            "quality and customer experience."
        ),
        templates=[
            _tpl(
                "Product Recommendation", "casual",
                "Recommend a product naturally",
                "I've been using {product_name} for "
                "{timeframe} and it's been great.\n\n"
                "What I like: {feature_1}, {feature_2}."
                "\n\nCheck it out: {product_url}",
            ),
            _tpl(
                "Shopping Advice", "empathetic",
                "Help with purchase decisions",
                "I was in the same boat!\n\n"
                "{product_name} stood out because "
                "{key_benefit}. {product_description}\n\n"
                "Link: {product_url}",
            ),
        ],
        icon="cart",
    ),
    SeedBundle(
        name="Fitness & Health",
        slug="fitness",
        description=(
            "Engage with fitness enthusiasts seeking "
            "workout advice and health products."
        ),
        keywords=[
            "how to", "best workout",
            "effective exercise", "fitness routine",
            "health tip",
        ],
        platforms=[
            "Reddit r/fitness", "Reddit r/running",
            "Reddit r/bodybuilding",
            "Reddit r/nutrition",
        ],
        tone="friendly",
        tone_description=(
            "Encouraging and supportive. "
            "Share personal experience. "
            "Avoid medical claims."
        ),
        templates=[
            _tpl(
                "Fitness Tip", "casual",
                "Share a fitness tip naturally",
                "I had the same question!\n\n"
                "What worked: {suggestion_1}. "
                "{product_name} helped because "
                "{product_description}.\n\n"
                "Check it out: {product_url}",
            ),
            _tpl(
                "Routine Share", "empathetic",
                "Share a workout routine",
                "Here's what I've been doing:\n\n"
                "1. {step_1}\n2. {step_2}\n"
                "3. {step_3}\n\n"
                "I track everything with "
                "{product_name}: {product_url}",
            ),
        ],
        icon="dumbbell",
    ),
    SeedBundle(
        name="Food & Restaurant",
        slug="food-restaurant",
        description=(
            "Connect with foodies and people "
            "looking for meal recommendations."
        ),
        keywords=[
            "best restaurant", "food recommendation",
            "recipe help", "meal delivery",
            "dining experience",
        ],
        platforms=[
            "Reddit r/food", "Reddit r/Cooking",
            "Reddit r/MealPrepSunday", "Yelp forums",
        ],
        tone="friendly",
        tone_description=(
            "Enthusiastic and personal. "
            "Share genuine food experiences."
        ),
        templates=[
            _tpl(
                "Food Recommendation", "casual",
                "Recommend food or restaurant",
                "You have to try this!\n\n"
                "{product_name} is amazing because "
                "{product_description}.\n\n"
                "Check it out: {product_url}",
            ),
            _tpl(
                "Recipe Share", "casual",
                "Share a recipe or cooking tip",
                "Here's my go-to approach:\n\n"
                "1. {step_1}\n2. {step_2}\n"
                "3. {step_3}\n\n"
                "Discovered via {product_name}: "
                "{product_url}",
            ),
        ],
        icon="utensils",
    ),
    SeedBundle(
        name="Travel & Tourism",
        slug="travel",
        description=(
            "Engage travelers planning trips "
            "and seeking destination advice."
        ),
        keywords=[
            "travel advice", "best destination",
            "trip planning", "hotel recommendation",
            "travel budget",
        ],
        platforms=[
            "Reddit r/travel", "Reddit r/solotravel",
            "Reddit r/TravelHacks",
            "TripAdvisor forums",
        ],
        tone="friendly",
        tone_description=(
            "Adventurous and personal. Share travel "
            "stories with practical details."
        ),
        templates=[
            _tpl(
                "Travel Tip", "casual",
                "Share travel advice",
                "I just went there!\n\n{suggestion_1}"
                "\n\n{product_name} helped with "
                "{product_description}.\n\n"
                "Details: {product_url}",
            ),
            _tpl(
                "Trip Planning Guide", "empathetic",
                "Help plan a trip",
                "Planning this kind of trip?\n\n"
                "1. {step_1}\n2. {step_2}\n"
                "3. {step_3}\n\n"
                "I used {product_name} to organize: "
                "{product_url}",
            ),
        ],
        icon="plane",
    ),
    SeedBundle(
        name="Parenting & Family",
        slug="parenting",
        description=(
            "Connect with parents seeking advice "
            "on childcare and family products."
        ),
        keywords=[
            "parenting advice", "best for kids",
            "child development",
            "family recommendation", "baby products",
        ],
        platforms=[
            "Reddit r/Parenting", "Reddit r/Mommit",
            "Reddit r/daddit",
        ],
        tone="friendly",
        tone_description=(
            "Empathetic and supportive. Share personal "
            "parenting experience. Never judge."
        ),
        templates=[
            _tpl(
                "Parenting Experience", "empathetic",
                "Share parenting experience",
                "I went through this with my kids!\n\n"
                "What helped: {suggestion_1}. "
                "{product_name} was great because "
                "{product_description}.\n\n"
                "Link: {product_url}",
            ),
            _tpl(
                "Family Product Review", "casual",
                "Review a family-friendly product",
                "We've been using {product_name} for "
                "{timeframe} and the kids love it.\n\n"
                "Best part: {key_benefit}.\n\n"
                "Check it out: {product_url}",
            ),
        ],
        icon="baby",
    ),
]
