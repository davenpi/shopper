import asyncio

import click

from shopper.agent import shop


@click.command()
@click.argument("url")
@click.option(
    "--size",
    "-s",
    default=None,
    help="Size to select (e.g. 'M', '10', '32x30').",
)
@click.option(
    "--color",
    "-c",
    default=None,
    help="Color preference (e.g. 'black', 'navy').",
)
@click.option(
    "--prefs",
    "-p",
    default=None,
    help="Any additional preferences as free text.",
)
@click.option(
    "--model",
    "-m",
    default="bu-2-0",
    help="Browser Use model (e.g. 'bu-1-0', 'bu-2-0').",
)
@click.option(
    "--headless",
    is_flag=True,
    default=False,
    help="Run the browser without a visible window.",
)
def cli(url, size, color, prefs, model, headless):
    """Add a product to cart from a URL."""
    asyncio.run(
        shop(
            url=url, size=size, color=color, prefs=prefs, model=model, headless=headless
        )
    )
