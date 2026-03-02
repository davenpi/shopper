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


def _build_task(
    url: str, size: str | None, color: str | None, prefs: str | None
) -> str:
    """Build the agent task prompt from user inputs.

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
        The full task prompt for the agent.
    """
    lines = [
        f"Go to {url} and add the product to the cart.",
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
    lines.append(
        f"{step}. Confirm the item is in the cart and report back what was added, the size, color, and price."
    )
    lines.append("")
    lines.append(
        "If a popup or modal appears inside a cross-origin iframe (e.g. email signup, "
        "discount offers from Attentive/Klaviyo), coordinate-click the X button to "
        "dismiss it immediately. Do NOT waste steps on index clicks, JS injection, or "
        "Escape for iframe popups."
    )
    lines.append("")
    lines.append(
        "Do NOT proceed to checkout or enter any payment information. Stop after adding to cart."
    )

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
    task = _build_task(url, size, color, prefs)
    click_echo(f"Task:\n{task}\n")

    sensitive_data = _load_sensitive_data()

    profile = BrowserProfile(headless=headless)
    browser = BrowserSession(browser_profile=profile)
    if model.startswith("gemini"):
        llm = ChatGoogle(model=model)
    else:
        llm = ChatBrowserUse(model=model)

    tools = Tools()
    tools.set_coordinate_clicking(True)

    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        tools=tools,
        sensitive_data=sensitive_data if sensitive_data else None,
    )

    click_echo("Starting agent...\n")
    result = await agent.run()

    final = result.final_result()
    if final:
        click_echo(f"\nResult: {final}")
    else:
        click_echo("\nAgent finished without a result.")

    return final


def click_echo(msg: str) -> None:
    """Print via click for consistent CLI output."""
    import click

    click.echo(msg)
