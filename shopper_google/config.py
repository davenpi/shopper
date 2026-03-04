from dataclasses import dataclass, field

DEFAULT_EXCLUDED_ACTIONS = [
    "drag_and_drop",
]


@dataclass(slots=True)
class GoogleComputerUseConfig:
    """Runtime settings for the Google Computer Use smoke flow."""

    model: str = "gemini-3-flash-preview"
    headless: bool = False
    screen_width: int = 1440
    screen_height: int = 900
    turn_limit: int = 15
    action_timeout_ms: int = 5_000
    post_action_sleep_s: float = 1.0
    excluded_actions: list[str] = field(
        default_factory=lambda: list(DEFAULT_EXCLUDED_ACTIONS)
    )
