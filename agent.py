
import re

from tools import (
    search_listings,
    suggest_outfit,
    create_fit_card,
    compare_price
)


# ── style memory (stretch feature) ───────────────────────────────────────────

STYLE_MEMORY = {

    "styles": []

}

def update_style_memory(query: str):

    known_styles = [
        "grunge",
        "streetwear",
        "y2k",
        "vintage",
        "cottagecore",
        "minimal"
    ]

    query_lower = query.lower()

    for style in known_styles:

        if style in query_lower:

            if style not in STYLE_MEMORY["styles"]:

                STYLE_MEMORY["styles"].append(style)
# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:

    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "price_analysis": None,
        "error": None,               # set if the interaction ended early
    }


def parse_query(query: str) -> dict:

    max_price = None
    size = None

    price_match = re.search(r"\$(\d+)", query)

    if price_match:
        max_price = float(price_match.group(1))

    size_match = re.search(
        r"\b(XXS|XS|S|M|L|XL|XXL)\b",
        query,
        re.IGNORECASE
    )

    if size_match:
        size = size_match.group(1)

    description = query

    if price_match:
        description = description.replace(
            price_match.group(0),
            ""
        )

    if size_match:
        description = description.replace(
            size_match.group(0),
            ""
        )

    description = (
        description
        .replace("under", "")
        .replace("size", "")
        .strip()
    )

    return {
        "description": description,
        "size": size,
        "max_price": max_price
    }

# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
        session = _new_session(query, wardrobe)
        update_style_memory(query)
        session["style_preferences"] = STYLE_MEMORY["styles"]
        parsed = parse_query(query)
        session["parsed"] = parsed
        results = search_listings(
            parsed["description"],
            parsed["size"],
            parsed["max_price"]
        )

        # Retry logic (bonus point)
        if not results:
            results = search_listings(
                parsed["description"],
                None,
                parsed["max_price"]
            )

        if not results:
            session["error"] = (
                "No matching listings were found. "
                "Try a broader description, different size, "
                "or higher budget."
            )
            return session

        session["search_results"] = results
        session["selected_item"] = results[0]
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"],
            wardrobe,
            session["style_preferences"]
        )

        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"],
            session["selected_item"]
        )

        session["price_analysis"] = compare_price(
            session["selected_item"]
        )

        return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")


    print(f"\nPrice Analysis:")
    print(session["price_analysis"])

    print("\n\n=== Empty Wardrobe Path ===\n")

    session3 = run_agent(
        query="vintage graphic tee under $30",
        wardrobe=get_empty_wardrobe()
    )

    if session3["error"]:
        print(session3["error"])
    else:
        print(session3["outfit_suggestion"])
        print("\n\n=== Retry Logic Test ===\n")
        session4 = run_agent(
            query="graphic tee size XXS under $30",
            wardrobe=get_example_wardrobe()
        )
        if session4["error"]:
            print(session4["error"])
        else:
            print(
                "Retry successful:",
                session4["selected_item"]["title"]
            )

