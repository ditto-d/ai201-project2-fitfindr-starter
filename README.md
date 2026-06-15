# FitFindr

FitFindr is an AI-powered secondhand fashion assistant that helps users discover thrifted clothing items, generate outfit recommendations using their wardrobe, evaluate whether a listing is fairly priced, and create social-media-ready outfit captions.

The agent combines traditional search, state management, and large language model reasoning to guide users from product discovery to outfit creation.

---

## Running the Project

**Gradio Interface (Required)**
```bash
python app.py
```

**Custom Flask Frontend (Optional)**
```bash
python server.py
```
Then open http://localhost:5000

---

## Tool Inventory

### Tool 1: search_listings

Searches the secondhand listings dataset and ranks results by relevance.

**Inputs**

| Parameter | Type |
|---|---|
| `description` | `str` |
| `size` | `str | None` |
| `max_price` | `float | None` |

**Output:** `list[dict]`

Each listing contains: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`

**Example**

Input:
```python
description="vintage graphic tee"
size=None
max_price=30
```
Output: A ranked list of matching listing dictionaries.

---

### Tool 2: suggest_outfit

Generates outfit recommendations using the selected listing and the user's wardrobe.

**Inputs**

| Parameter | Type |
|---|---|
| `new_item` | `dict` |
| `wardrobe` | `dict` |

**Output:** `str`

**Example**

Input: Selected listing "Vintage Band Tee" with wardrobe containing baggy jeans, chunky sneakers, denim jacket.

Output: A complete outfit recommendation using the named wardrobe pieces.

---

### Tool 3: create_fit_card

Creates a social-media style outfit caption.

**Inputs**

| Parameter | Type |
|---|---|
| `outfit` | `str` |
| `new_item` | `dict` |

**Output:** `str`

**Example**

> "Just scored this vintage band tee for $19 on Depop and paired it with baggy jeans and chunky sneakers..."

---

### Tool 4: compare_price

Determines whether a listing is fairly priced.

**Inputs**

| Parameter | Type |
|---|---|
| `item` | `dict` |

**Output:** `str`

**Example**

> Average comparable price: $22.00. Assessment: Fair Price.

---

## Planning Loop

The agent follows a deterministic planning loop.

1. Parse the user query
2. Extract description, size, and maximum price
3. Call `search_listings()`
4. If no results are found, retry the search without the size filter
5. If no results are found after retrying, set `session["error"]` and stop execution
6. Select the highest ranked listing
7. Store the listing in `session["selected_item"]`
8. Call `suggest_outfit()`
9. Store the result in `session["outfit_suggestion"]`
10. Call `create_fit_card()`
11. Store the result in `session["fit_card"]`
12. Call `compare_price()`
13. Store the result in `session["price_analysis"]`
14. Return the completed session

This conditional logic allows the agent to recover from overly restrictive searches before failing.

---

## State Management

The application uses a session dictionary as the single source of truth.

**Stored values:** `query`, `parsed`, `search_results`, `selected_item`, `wardrobe`, `outfit_suggestion`, `fit_card`, `price_analysis`, `error`

State is passed between tools through the session object:

- `search_listings()` stores the selected item in `session["selected_item"]`
- `suggest_outfit()` reads that value and produces `session["outfit_suggestion"]`
- `create_fit_card()` uses `session["outfit_suggestion"]` without requiring additional user input

This demonstrates state persistence across multiple tool calls.

---

## Error Handling

| Tool | Failure | Response |
|---|---|---|
| `search_listings` | No matching results | Retries without size filter. If still empty, returns error message. |
| `suggest_outfit` | Empty wardrobe | Generates general styling advice instead. |
| `create_fit_card` | Missing outfit | Returns descriptive error, does not crash. |
| `compare_price` | No comparable listings | Returns unavailable message and continues. |

**search_listings example**

Query: `"graphic tee size XXS under $30"` — first search returned no results. Agent removed size filter and successfully returned a matching listing.

If no matches exist after retrying: `"No matching listings were found. Try a broader description, different size, or higher budget."`

**create_fit_card example**

`create_fit_card("", item)` returns: `"Unable to generate fit card because no outfit suggestion was available."`

---

## Spec Reflection

**How the specification helped**

The planning document helped define the tool interfaces before implementation. By deciding inputs, outputs, and failure modes first, implementation became significantly easier and more structured.

**How implementation diverged from the specification**

The original specification only required three tools. During implementation a fourth tool, `compare_price()`, was added because price evaluation provides useful context when purchasing secondhand clothing. This feature also demonstrated additional tool orchestration and state management.

---

## AI Usage

**Example 1**

Tool Used: ChatGPT

Input Provided: The Tool 1 specification from planning.md including inputs, outputs, ranking behavior, and failure handling.

Output Produced: A rough skeleton for keyword-overlap scoring in `search_listings()`.

Changes Made: The output was incomplete and did not match my spec. I used it only as a reference while writing the actual implementation myself. I built the filtering logic, designed the scoring approach, and added the retry behavior based on my own planning loop. ChatGPT did not produce working code for this tool.

**Example 2**

Tool Used: ChatGPT

Input Provided: The Planning Loop section, State Management section, and Architecture Diagram from planning.md.

Output Produced: A rough outline of how `run_agent()` could be structured.

Changes Made: I wrote `run_agent()` myself using my planning.md as the guide. The AI output helped me confirm I was not missing any steps, but the session state design, the fallback search logic, and the integration of all four tools were decisions I made and implemented on my own.

---

## Demo Scenarios

**Happy Path**

Query: `"vintage graphic tee under $30"`

Result: Listing found, outfit generated, fit card generated, price analysis generated.

**Retry Path**

Query: `"graphic tee size XXS under $30"`

Result: Initial search failed, agent removed size filter, listing successfully found.

**Empty Wardrobe Path**

Query: `"vintage graphic tee under $30"` with empty wardrobe

Result: Listing found, general styling advice generated, fit card generated.

**Failure Path**

Query: `"designer ballgown size XXS under $5"`

Result: `"No matching listings were found. Try a broader description, different size, or higher budget."`

---

## Testing

**No Results Found**

Query: `designer ballgown size XXS under $5`

Result: Agent retried without size filter then returned the no-results error message.

**Empty Wardrobe**

Result: Agent generated general styling advice instead of referencing wardrobe items.

**Missing Outfit Suggestion**

`create_fit_card("", item)` returned: `"Unable to generate fit card because no outfit suggestion was available."`

**Automated Testing**

Pytest was used to validate tool behavior. 6/6 tests passed.

- search returns results
- search returns empty list
- price filter works
- empty wardrobe handling
- fit card generation
- fit card failure handling