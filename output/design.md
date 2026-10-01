# Design Notes (Problem 10)

Quick description of each change and why customers would like it.

- **Rotating homepage banner** — The hero now cycles through the three Fan Favorite product photos (crossfade, with click-through dots) instead of a flat navy block. Gives first-time visitors real product imagery immediately, not just a logo and text.

- **Bulldog cursor** — The mouse pointer is a small bulldog-face icon (hand-drawn SVG) everywhere on the site. A fun, on-brand touch that makes the site feel distinctly "Campus Customs" rather than generic.

- **Best-seller ordering on the Products page** — Products are now sorted with the lowest-remaining-stock items first, badged "Best Seller." *(Assumption, documented here since there's no real sales/orders table: lower remaining stock stands in for "sold the most," not an actual sales count.)* Helps customers quickly find what's popular instead of scanning alphabetically.

- **Clean sans-serif type everywhere** — Replaced the serif headings with a system sans-serif stack (`--cc-font`) used consistently for every heading and body element. Reads as modern and easy to scan, not like a default template.

- **Lighter blue toolbar + chat accents** — The top nav and chat widget now use a lighter accent blue (`--cc-light-blue`) against the deeper navy used elsewhere, so the toolbar visually pops and stays easy to find while scrolling, and the chat widget reads as connected to it.

- **Chat "feel" polish** — Messages now fade/slide in individually and have asymmetric bubble corners (a small flat corner on the side each message "points" from), closer to a real messaging app than plain rectangles.

- **Best-seller badges + product card hover lift** — Small "Best Seller" pill on top cards, plus a subtle lift-and-shadow on hover across every product card, giving clear visual feedback that cards are clickable.
