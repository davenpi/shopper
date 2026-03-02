import os

from browser_use import Agent, BrowserSession, Tools
from browser_use.browser.profile import BrowserProfile
from browser_use.llm import ChatBrowserUse, ChatGoogle
from dotenv import load_dotenv

load_dotenv()
os.environ["ANONYMIZED_TELEMETRY"] = "false"

# Keys that map to .env variables for sensitive_data injection.
# The LLM sees these key names as placeholders, never the real values.
_SENSITIVE_KEYS = [
    "SHIPPING_FIRST_NAME",
    "SHIPPING_LAST_NAME",
    "SHIPPING_ADDRESS",
    "SHIPPING_CITY",
    "SHIPPING_STATE",
    "SHIPPING_ZIP",
    "SHIPPING_PHONE",
    "SHIPPING_EMAIL",
    "CARD_NUMBER",
    "CARD_EXP",
    "CARD_CVV",
    "CARD_NAME",
]


def _load_sensitive_data() -> dict[str, str]:
    """Load sensitive checkout data from environment variables.

    Returns
    -------
    dict[str, str]
        Mapping of placeholder key to secret value. Only keys that are
        actually set in the environment are included.
    """
    data = {}
    for key in _SENSITIVE_KEYS:
        val = os.environ.get(key)
        if val:
            data[key] = val
    return data


def _build_shopping_task(
    url: str, size: str | None, color: str | None, prefs: str | None
) -> str:
    """Build the task prompt for the shopping agent (add to cart + go to checkout).

    Parameters
    ----------
    url : str
        Product page URL.
    size : str or None
        Desired size.
    color : str or None
        Desired color.
    prefs : str or None
        Additional free-text preferences.

    Returns
    -------
    str
        The full task prompt for the shopping agent.
    """
    lines = [
        f"Go to {url} and add the product to the cart, then proceed to checkout.",
        "",
        "Steps:",
        "1. Navigate to the product page.",
    ]

    step = 2
    if color:
        lines.append(f"{step}. Select color: {color}.")
        step += 1
    if size:
        lines.append(f"{step}. Select size: {size}.")
        step += 1
    if prefs:
        lines.append(f"{step}. Apply these preferences: {prefs}")
        step += 1

    lines.append(f"{step}. Click 'Add to Cart' (or equivalent button).")
    step += 1
    lines.append(f"{step}. Proceed to checkout.")
    lines.append("")
    lines.append(
        "If a popup or modal appears inside a cross-origin iframe (e.g. email signup, "
        "discount offers from Attentive/Klaviyo), coordinate-click the X button to "
        "dismiss it immediately. Do NOT waste steps on index clicks, JS injection, or "
        "Escape for iframe popups."
    )
    lines.append("")
    lines.append(
        "Before proceeding to checkout, verify the cart contains exactly 1 of the "
        "correct item in the right size/color. Remove any duplicates or wrong items."
    )
    lines.append("")
    lines.append(
        "Do NOT fill in any shipping or payment information. "
        "Stop once the checkout page has loaded."
    )

    return "\n".join(lines)


def _build_checkout_task(sensitive_keys: list[str]) -> str:
    """Build the task prompt for the checkout agent (fill forms, no submit).

    Parameters
    ----------
    sensitive_keys : list[str]
        The placeholder keys that are available in sensitive_data.
        Only these are referenced in the prompt.

    Returns
    -------
    str
        The full task prompt for the checkout agent.
    """
    shipping_keys = [k for k in sensitive_keys if k.startswith("SHIPPING_")]
    card_keys = [k for k in sensitive_keys if k.startswith("CARD_")]

    lines = ["Fill in the checkout form.", "", "Steps:"]
    step = 1

    if shipping_keys:
        lines.append(
            f"{step}. Fill in shipping information using: "
            + ", ".join(shipping_keys)
            + "."
        )
        step += 1

    if card_keys:
        lines.append(
            f"{step}. Fill in payment information using: " + ", ".join(card_keys) + "."
        )
        step += 1

    lines.append(
        f"{step}. STOP before placing the order. Report back the order summary "
        "including item, size, color, price, and total."
    )
    lines.append("")
    lines.append("Do NOT click 'Place Order' or any final submit button.")

    return "\n".join(lines)


async def shop(
    url: str,
    size: str | None = None,
    color: str | None = None,
    prefs: str | None = None,
    model: str = "bu-2-0",
    headless: bool = False,
) -> str | None:
    """Run the shopping agent to add a product to cart.

    Parameters
    ----------
    url : str
        Product page URL.
    size : str or None
        Desired size.
    color : str or None
        Desired color.
    prefs : str or None
        Additional free-text preferences.
    model : str
        Browser Use model ID.
    headless : bool
        Run the browser without a visible window.

    Returns
    -------
    str or None
        The agent's final result summary.
    """
    sensitive_data = _load_sensitive_data()

    shopping_task = _build_shopping_task(url, size, color, prefs)
    click_echo(f"Shopping task:\n{shopping_task}\n")

    profile = BrowserProfile(headless=headless, keep_alive=True)
    browser = BrowserSession(browser_profile=profile)
    if model.startswith("gemini"):
        llm = ChatGoogle(model=model)
    else:
        llm = ChatBrowserUse(model=model)

    tools = Tools()
    tools.set_coordinate_clicking(True)

    # Phase 1: shopping agent (vision ON) — add to cart, navigate to checkout.
    shopping_agent = Agent(
        task=shopping_task,
        llm=llm,
        browser=browser,
        tools=tools,
    )

    click_echo("Starting shopping agent...\n")
    result = await shopping_agent.run()

    shopping_result = result.final_result()
    if not shopping_result:
        click_echo("\nShopping agent finished without a result.")
        return None
    click_echo(f"\nShopping result: {shopping_result}\n")

    # Phase 2: checkout agent (vision OFF) — fill forms with sensitive data.
    checkout_task = _build_checkout_task(list(sensitive_data.keys()))
    click_echo(f"Checkout task:\n{checkout_task}\n")

    checkout_agent = Agent(
        task=checkout_task,
        llm=llm,
        browser=browser,
        tools=tools,
        sensitive_data=sensitive_data,
        use_vision=False,
    )

    click_echo("Starting checkout agent...\n")
    try:
        result = await checkout_agent.run()
    finally:
        await browser.kill()

    final = result.final_result()
    if final:
        click_echo(f"\nResult: {final}")
    else:
        click_echo("\nCheckout agent finished without a result.")

    return final


def click_echo(msg: str) -> None:
    """Print via click for consistent CLI output."""
    import click

    click.echo(msg)
