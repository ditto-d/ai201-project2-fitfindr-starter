

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:

    listings = load_listings()
    query_words = set(description.lower().split())
    scored_results = []

    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue

        if size is not None:
            if size.lower() not in listing["size"].lower():
                continue

        searchable_text = " ".join([
            listing["title"],
            listing["description"],
            listing["category"],
            " ".join(listing["style_tags"]),
            " ".join(listing["colors"])

        ]).lower()

        score = sum( 1 for word in query_words if word in searchable_text )

        if score > 0:
            scored_results.append((score, listing))

    scored_results.sort( key=lambda x: x[0],reverse=True )
    return [listing for score, listing in scored_results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict,wardrobe: dict,style_preferences: list | None = None) -> str:

        client = _get_groq_client()

        style_text = (
            ", ".join(style_preferences)
            if style_preferences
            else "None"
        )

        wardrobe_items = wardrobe.get("items", [])

        if not wardrobe_items:

            prompt = f"""
        The user has no wardrobe information.

        Known user style preferences:
        {style_text}

        If style preferences exist, prioritize those aesthetics.

        Item:
        Title: {new_item['title']}
        Category: {new_item['category']}
        Style Tags: {", ".join(new_item['style_tags'])}
        Colors: {", ".join(new_item['colors'])}

        Give 2 styling suggestions.

        Requirements:
        - Mention bottoms, shoes, and accessories.
        - Explain the vibe.
        - Incorporate preferred styles when relevant.
        - Keep under 150 words.
        """

        else:

            wardrobe_text = "\n".join(
                [
                    f"- {item['name']} "
                    f"({item['category']}) "
                    f"[{', '.join(item['style_tags'])}]"
                    for item in wardrobe_items
                ]
            )

            prompt = f"""
        You are a fashion styling assistant.

        Known user style preferences:
        {style_text}

        Prioritize those aesthetics when creating outfits.

        New thrifted item:
        Title: {new_item['title']}
        Category: {new_item['category']}
        Style Tags: {", ".join(new_item['style_tags'])}
        Colors: {", ".join(new_item['colors'])}

        User wardrobe:
        {wardrobe_text}

        Create 1-2 complete outfit combinations.

        Requirements:
        - Use actual wardrobe items by name.
        - Explain why the pieces work together.
        - Mention shoes if available.
        - Mention the overall aesthetic.
        - Incorporate preferred styles.
        - Keep under 200 words.
        """

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Unable to generate outfit suggestion: {str(e)}"

# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return ( "Unable to generate fit card because no outfit "
                "suggestion was available.")

    client = _get_groq_client()
    prompt = f""" Create a short social-media outfit caption.

    Item:
    - Name: {new_item['title']}
    - Price: ${new_item['price']}
    - Platform: {new_item['platform']}

    Outfit: {outfit}

    Requirements:
    - 2 to 4 sentences
    - Casual and authentic
    - Mention item name once
    - Mention price once
    - Mention platform once
    - Sound like a real outfit post
    - Not a product advertisement
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
            return f"Unable to generate fit card: {str(e)}"


def compare_price(item: dict) -> str:

    listings = load_listings()

    comparable = [
        listing["price"]
        for listing in listings
        if listing["category"] == item["category"]
        and listing["id"] != item["id"]
    ]

    if not comparable:
        return (
            "Not enough comparable listings available "
            "to estimate price fairness."
        )

    avg_price = sum(comparable) / len(comparable)

    difference = item["price"] - avg_price

    if difference < -5:
        verdict = "Good deal"
    elif difference > 5:
        verdict = "Slightly overpriced"
    else:
        verdict = "Fair price"

    return (
        f"Average comparable price: ${avg_price:.2f}. "
        f"This item is ${abs(difference):.2f} "
        f"{'below' if difference < 0 else 'above'} average. "
        f"Assessment: {verdict}."
    )

if __name__ == "__main__":

    from utils.data_loader import (
        get_example_wardrobe,
        get_empty_wardrobe
    )

    results = search_listings(
        "vintage graphic tee",
        None,
        30
    )

    print("=== SEARCH RESULTS ===")
    for item in results[:3]:
        print(item["title"], "-", item["price"])

    print("\n=== OUTFIT TEST ===")
    outfit = suggest_outfit(
        results[0],
        get_example_wardrobe()
    )

    print(outfit)

    print("\n=== EMPTY WARDROBE TEST ===")
    print(
        suggest_outfit(
            results[0],
            get_empty_wardrobe()
        )
    )

    print("\n=== FIT CARD TEST ===")
    print(
        create_fit_card(
            outfit,
            results[0]
        )
    )

    print("\n=== FIT CARD FAILURE TEST ===")

    print(

        create_fit_card(

            "",

            results[0]

        )

    )

