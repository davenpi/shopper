import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import click
from dotenv import load_dotenv

from shopper_google.config import GoogleComputerUseConfig
from shopper_google.prompts import build_shopping_prompt
from shopper_google.runner import GoogleComputerUseRunner


class Tee:
    """Mirror writes to the console and a log file."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


@click.command()
@click.argument("url")
@click.option("--size", default=None, help="Size to select, e.g. 'M 9.5'.")
@click.option(
    "--model",
    default="gemini-3-flash-preview",
    show_default=True,
    help="Google Gemini Computer Use model.",
)
@click.option(
    "--headless",
    is_flag=True,
    default=False,
    help="Run Chromium without a visible window.",
)
@click.option(
    "--turn-limit",
    default=15,
    show_default=True,
    type=int,
    help="Maximum Computer Use turns before stopping.",
)
@click.option(
    "--log-file",
    default="logs/google-latest.log",
    show_default=True,
    help="File to tee console logs into.",
)
def smoke(
    url: str,
    size: str | None,
    model: str,
    headless: bool,
    turn_limit: int,
    log_file: str,
) -> None:
    """Run the Google Computer Use shopping-only smoke test."""

    load_dotenv()

    config = GoogleComputerUseConfig(
        model=model,
        headless=headless,
        turn_limit=turn_limit,
    )
    prompt = build_shopping_prompt(url=url, size=size)
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", encoding="utf-8") as log_stream:
        tee = Tee(sys.stdout, log_stream)
        with redirect_stdout(tee), redirect_stderr(tee):
            click.echo(f"Prompt:\n{prompt}\n")
            click.echo(f"Logging to {log_path}")
            runner = GoogleComputerUseRunner(config)
            result = runner.run(prompt=prompt, initial_url=url)
            click.echo(f"\nFinal result ({result.turns} turns): {result.final_text}")
