from dataclasses import dataclass

from google import genai
from google.genai import types

from shopper_google.actions import build_function_response_parts, execute_function_calls
from shopper_google.browser import BrowserEnvironment
from shopper_google.config import GoogleComputerUseConfig


@dataclass(slots=True)
class RunResult:
    """Final result of a Google Computer Use run."""

    final_text: str
    turns: int


class GoogleComputerUseRunner:
    """Run a Gemini Computer Use loop against a Playwright browser."""

    def __init__(self, config: GoogleComputerUseConfig):
        self.config = config
        self.client = genai.Client()

    def run(self, prompt: str, initial_url: str) -> RunResult:
        with BrowserEnvironment(self.config) as env:
            if env.page is None:
                raise RuntimeError("Browser page is not initialized")

            env.page.goto(initial_url)
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part(text=prompt),
                        types.Part.from_bytes(
                            data=env.screenshot(),
                            mime_type="image/png",
                        ),
                    ],
                )
            ]

            config = types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        computer_use=types.ComputerUse(
                            environment=types.Environment.ENVIRONMENT_BROWSER,
                            excluded_predefined_functions=self.config.excluded_actions,
                        )
                    )
                ]
            )

            for turn in range(1, self.config.turn_limit + 1):
                response = self.client.models.generate_content(
                    model=self.config.model,
                    contents=contents,
                    config=config,
                )
                candidate = response.candidates[0]
                contents.append(candidate.content)

                text_chunks = [
                    part.text
                    for part in candidate.content.parts
                    if getattr(part, "text", None)
                ]
                if text_chunks:
                    print(f"\nModel: {' '.join(text_chunks)}")

                has_function_calls = any(
                    getattr(part, "function_call", None) is not None
                    for part in candidate.content.parts
                )
                if not has_function_calls:
                    return RunResult(
                        final_text=" ".join(text_chunks).strip(), turns=turn
                    )

                for part in candidate.content.parts:
                    function_call = getattr(part, "function_call", None)
                    if function_call is None:
                        continue
                    print(
                        f"Action: {function_call.name} {dict(function_call.args or {})}"
                    )

                results = execute_function_calls(candidate, env, self.config)
                contents.append(
                    types.Content(
                        role="user",
                        parts=build_function_response_parts(env, results),
                    )
                )

            raise RuntimeError(
                f"Reached turn limit ({self.config.turn_limit}) without a final answer"
            )
