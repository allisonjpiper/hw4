# Usability Improvements (Problem 9)

Two frontend improvements and two backend/agent improvements, each already live in the running app (not just described).

## Frontend

### 1. Homepage "Fan Favorites" photo strip

**What was added:** A "Fan Favorites" section on the Home page (`frontend/src/pages/Home.tsx`), between the hero banner and the "What We're About" copy — three of the site's own real product photos (Basic Hoodie Big Yale, the 2025 Yale Vs Harvard Tee, and the Boola Boola Tee), each a clickable card linking straight to that product's detail page.

*(First pass used generic Unsplash lifestyle photos of people in casual wear. Real photos of people actually wearing Yale-branded merch aren't available as free stock content — that's licensed/trademarked apparel, not generic stock photography — so this was swapped for the site's own genuine product photography instead, which is both authentically "Yale spirit gear" and already fully rights-cleared.)*

**Why it helps:** A wall of navy-and-white text and a "browse everything" link reads as a placeholder, not a real shop. Leading with three specific, clickable products gives a first-time visitor an immediate, low-effort way into the catalogue instead of making them find the Products page first — and because these are real catalogue items, every click is a genuine path toward a sale, not just decoration.

### 2. Smooth "iMessage-style" chat bubble expand

**What was added:** The floating chat panel (`frontend/src/components/ChatWidget.tsx` + `.css`) now always stays mounted and animates open/closed with a CSS transform+opacity transition — collapsing down near the toggle button when closed and popping open with a slight overshoot (`cubic-bezier(0.34, 1.56, 0.64, 1)`) when opened, instead of instantly appearing/disappearing.

**Why it helps:** An instant pop-in feels broken or laggy; a chat bubble that visibly expands from the corner (the way iMessage/most modern chat widgets animate) reads as polished and gives the customer a clear visual anchor for where the chat "lives" on the page, making them more likely to actually use it instead of assuming it's a static decoration.

## Backend / Agent

### 1. `product_info_from_message` — pull product info directly from the customer's own wording

**What was added:** A new agent tool (`backend/tools.py: product_info_from_message`, wired in `backend/agent.py`) that takes the customer's raw chat message — a full sentence, not a search keyword — and returns full real product info (description, price, per-size stock) for whatever it matches, ranked by keyword-token overlap with the message. Previously the agent needed two separate tool calls (`search_products` then `product_lookup`) chained together itself; this fuses that into one call keyed directly off what the customer actually typed.

**Why it helps:** Fewer tool round-trips per turn means faster replies and lower LLM cost per conversation (fewer requests against `UsageLimits`), and it's more robust — the agent doesn't have to first decide "is this a search or a lookup" for an ordinary sentence like "is the basic hoodie big yale in stock", it can just hand the whole message to one tool and get a grounded answer back.

### 2. Category-sorted product index for faster, more precise browsing

**What was added:** `backend/tools.py: normalize_category`, `list_categories`, and `search_products_by_category` group the catalogue's 21 granular `garment_type` values (e.g. "hooded pullover sweatshirt", "pullover hoodie", "hoodie") into 6 customer-facing categories (Hoodie, Crewneck, T-Shirt, Quarter-Zip, Outerwear, Long Sleeve), sorted category-then-name. The prompt now tells the agent to call `search_products_by_category` first whenever a customer names a garment type, instead of falling back to the broader multi-field keyword scan in `search_products`.

**Why it helps:** A customer asking "what hoodies do you have" is asking a category question, not a fuzzy-text one — matching directly against a normalized category is both faster (no need to substring-scan name/description/colors/tags across all 102 rows) and more precise (it won't accidentally pull in a t-shirt whose description happens to mention "hood" in passing). For the business, that's more consistent, predictable browsing results as the catalogue grows past 102 items.
