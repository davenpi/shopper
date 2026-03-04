import sys
import time
from dataclasses import dataclass, field
from typing import Any

from google.genai import types

from shopper_google.browser import BrowserEnvironment
from shopper_google.config import GoogleComputerUseConfig


def denormalize_x(x: int, screen_width: int) -> int:
    """Convert a normalized x coordinate into viewport pixels."""

    return int(x / 1000 * screen_width)


def denormalize_y(y: int, screen_height: int) -> int:
    """Convert a normalized y coordinate into viewport pixels."""

    return int(y / 1000 * screen_height)


@dataclass(slots=True)
class ActionResult:
    """A single executed model action and the data returned to Gemini."""

    name: str
    response: dict[str, Any] = field(default_factory=dict)


def _meta_key() -> str:
    return "Meta" if sys.platform == "darwin" else "Control"


def _wait_for_page_settle(
    env: BrowserEnvironment, timeout_ms: int, sleep_s: float
) -> None:
    if env.page is None:
        raise RuntimeError("Browser page is not initialized")
    try:
        env.page.wait_for_load_state(timeout=timeout_ms)
    except Exception:
        # Dynamic commerce pages often never fully settle; keep moving.
        pass
    time.sleep(sleep_s)


def _maybe_confirm_safety(args: dict[str, Any]) -> dict[str, Any]:
    safety = args.get("safety_decision")
    if not safety:
        return {}
    if safety.get("decision") != "require_confirmation":
        return {}

    print("\nSafety confirmation required:")
    print(safety.get("explanation", "No explanation provided."))
    answer = input("Proceed with this action? [y/N]: ").strip().lower()
    if answer not in {"y", "yes"}:
        raise RuntimeError("User denied a safety-gated action")
    return {"safety_acknowledgement": "true"}


def execute_function_calls(
    candidate: Any,
    env: BrowserEnvironment,
    config: GoogleComputerUseConfig,
) -> list[ActionResult]:
    """Execute all function calls returned in a Gemini candidate."""

    if env.page is None:
        raise RuntimeError("Browser page is not initialized")

    results: list[ActionResult] = []
    function_calls = [
        part.function_call
        for part in candidate.content.parts
        if getattr(part, "function_call", None) is not None
    ]

    for function_call in function_calls:
        name = function_call.name
        args = dict(function_call.args or {})
        response: dict[str, Any] = {}

        try:
            response.update(_maybe_confirm_safety(args))

            if name == "open_web_browser":
                pass
            elif name == "wait_5_seconds":
                time.sleep(5)
            elif name == "go_back":
                env.page.go_back()
            elif name == "go_forward":
                env.page.go_forward()
            elif name == "search":
                env.page.goto("https://www.google.com")
            elif name == "navigate":
                env.page.goto(args["url"])
            elif name == "click_at":
                env.page.mouse.click(
                    denormalize_x(args["x"], config.screen_width),
                    denormalize_y(args["y"], config.screen_height),
                )
            elif name == "hover_at":
                env.page.mouse.move(
                    denormalize_x(args["x"], config.screen_width),
                    denormalize_y(args["y"], config.screen_height),
                )
            elif name == "type_text_at":
                x = denormalize_x(args["x"], config.screen_width)
                y = denormalize_y(args["y"], config.screen_height)
                clear_before_typing = args.get("clear_before_typing", True)
                press_enter = args.get("press_enter", True)
                env.page.mouse.click(x, y)
                if clear_before_typing:
                    env.page.keyboard.press(f"{_meta_key()}+A")
                    env.page.keyboard.press("Backspace")
                env.page.keyboard.type(args["text"])
                if press_enter:
                    env.page.keyboard.press("Enter")
            elif name == "key_combination":
                env.page.keyboard.press(args["keys"])
            elif name == "scroll_document":
                _scroll_document(env, args["direction"])
            elif name == "scroll_at":
                _scroll_at(env, config, args)
            elif name == "drag_and_drop":
                _drag_and_drop(env, config, args)
            else:
                raise NotImplementedError(f"Unsupported Computer Use action: {name}")

            _wait_for_page_settle(
                env,
                timeout_ms=config.action_timeout_ms,
                sleep_s=config.post_action_sleep_s,
            )
        except Exception as exc:
            response["error"] = str(exc)

        results.append(ActionResult(name=name, response=response))

    return results


def build_function_response_parts(
    env: BrowserEnvironment, results: list[ActionResult]
) -> list[types.Part]:
    """Build the user turn parts that return execution results to Gemini."""

    screenshot = env.screenshot()
    current_url = env.current_url()
    parts: list[types.Part] = []

    for result in results:
        response = {"url": current_url}
        response.update(result.response)
        parts.append(
            types.Part(
                function_response=types.FunctionResponse(
                    name=result.name,
                    response=response,
                    parts=[
                        types.FunctionResponsePart(
                            inline_data=types.FunctionResponseBlob(
                                mime_type="image/png",
                                data=screenshot,
                            )
                        )
                    ],
                )
            )
        )

    return parts


def _scroll_document(env: BrowserEnvironment, direction: str) -> None:
    if env.page is None:
        raise RuntimeError("Browser page is not initialized")

    dx, dy = {
        "up": (0, -700),
        "down": (0, 700),
        "left": (-700, 0),
        "right": (700, 0),
    }[direction]
    env.page.mouse.wheel(dx, dy)


def _scroll_at(
    env: BrowserEnvironment, config: GoogleComputerUseConfig, args: dict[str, Any]
) -> None:
    if env.page is None:
        raise RuntimeError("Browser page is not initialized")

    x = denormalize_x(args["x"], config.screen_width)
    y = denormalize_y(args["y"], config.screen_height)
    magnitude = int(args.get("magnitude", 800) / 1000 * 900)
    direction = args["direction"]

    env.page.mouse.move(x, y)
    dx, dy = {
        "up": (0, -magnitude),
        "down": (0, magnitude),
        "left": (-magnitude, 0),
        "right": (magnitude, 0),
    }[direction]
    env.page.mouse.wheel(dx, dy)


def _drag_and_drop(
    env: BrowserEnvironment, config: GoogleComputerUseConfig, args: dict[str, Any]
) -> None:
    if env.page is None:
        raise RuntimeError("Browser page is not initialized")

    env.page.mouse.move(
        denormalize_x(args["x"], config.screen_width),
        denormalize_y(args["y"], config.screen_height),
    )
    env.page.mouse.down()
    env.page.mouse.move(
        denormalize_x(args["destination_x"], config.screen_width),
        denormalize_y(args["destination_y"], config.screen_height),
    )
    env.page.mouse.up()
