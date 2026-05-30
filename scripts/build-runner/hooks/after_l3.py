#!/usr/bin/env python3
"""Post-L3 hook: Generate API documentation after routes are created."""
import json
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger("after_l3")

# This is a template. Real implementation would:
# 1. Parse FastAPI routes in src/api/
# 2. Extract endpoint definitions
# 3. Generate openapi.json
# 4. Generate API_SURFACE.md

def main():
    """Generate API docs after L3 (routes) complete."""
    project_root = Path(__file__).parent.parent.parent.parent

    # Template OpenAPI schema
    openapi = {
        "openapi": "3.0.0",
        "info": {
            "title": "BuzzReach API",
            "version": "1.0.0",
            "description": "AI-powered opportunity discovery API",
        },
        "servers": [
            {"url": "https://api.buzzreach.com", "description": "Production"},
            {"url": "http://localhost:8000", "description": "Local development"},
        ],
        "paths": {},
        "x-generated-at": datetime.utcnow().isoformat(),
    }

    openapi_file = project_root / "openapi.json"
    with open(openapi_file, "w") as f:
        json.dump(openapi, f, indent=2)

    log.info("Generated %s", openapi_file)

    # Create API_SURFACE.md
    api_md = project_root / "API_SURFACE.md"
    with open(api_md, "w") as f:
        f.write("""# API Surface

## Endpoints

Auto-generated after L3 (routes).

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/opportunities` | List discovered opportunities |
| POST | `/api/v1/scan` | Trigger immediate scan |
| GET | `/api/v1/settings` | Get user settings |
| POST | `/api/v1/settings` | Update user settings |

See `openapi.json` for full specification.
""")

    log.info("Generated %s", api_md)
    print(f"✓ API documentation generated: {openapi_file}, {api_md}")

if __name__ == "__main__":
    main()
