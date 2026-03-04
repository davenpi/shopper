def build_shopping_prompt(url: str, size: str | None) -> str:
    """Return a shopping-only Computer Use prompt for Google testing."""

    lines = [
        f"Go to {url}.",
        "Add exactly one of the product to cart and stop after verifying the cart.",
        "Do not fill shipping information or payment information.",
        "Do not place an order.",
        "",
        "Rules:",
        "1. Match the requested size exactly.",
        "2. If a popup blocks the page, dismiss it.",
        "3. Verify the cart contains exactly one correct item before finishing.",
        "4. When the item is in cart and verified, summarize what happened and stop.",
    ]

    if size:
        lines.insert(1, f"Select size: {size}.")

    return "\n".join(lines)
