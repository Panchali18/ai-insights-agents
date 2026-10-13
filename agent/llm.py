"""Model wrapper. The rest of the agent only calls `generate`, so the provider can be swapped
in config.yaml without changing the agent's logic (US-7.2)."""

import os
import time


class CallLimitReached(RuntimeError):
    pass


def _is_server_side(error: Exception, message: str) -> bool:
    """True for failures on the provider's side (5xx, overload, deadline, timeout), which are worth
    retrying on another model. False for problems with our request or key."""
    if "timeout" in type(error).__name__.lower() or "timed out" in message.lower():
        return True
    markers = ("500", "502", "503", "504", "UNAVAILABLE", "DEADLINE_EXCEEDED", "INTERNAL", "overloaded")
    return any(marker in message for marker in markers)


class LLM:
    def __init__(self, model_config: dict):
        self.provider = model_config["provider"]
        self.model_name = model_config["name"]
        self.fallback_model = model_config.get("fallback_name")
        self.ranking_model = model_config.get("ranking_name") or self.model_name
        self.max_calls = model_config.get("max_calls_per_run", 5)
        self.timeout_seconds = model_config.get("timeout_seconds", 180)
        self.calls_made = 0

        api_key = os.environ.get(model_config["api_key_env"])
        if not api_key:
            raise SystemExit(
                f"No API key found. Add a secret called {model_config['api_key_env']} "
                "in your repo's Codespaces settings, then rebuild or restart the codespace."
            )

        if self.provider == "gemini":
            from google import genai
            from google.genai import types

            # One library-level retry only: on a server error we switch to the fallback model
            # ourselves, rather than waiting through several silent retries of the same model.
            self._client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=self.timeout_seconds * 1000,
                    retry_options=types.HttpRetryOptions(attempts=2),
                ),
            )
        else:
            raise SystemExit(f"Provider '{self.provider}' is not supported yet.")

    def list_models(self) -> list:
        """Names of the models this key can use for text generation (no generation call is made)."""
        names = []
        for model in self._client.models.list():
            actions = getattr(model, "supported_actions", None) or []
            if not actions or "generateContent" in actions:
                names.append(model.name.removeprefix("models/"))
        return sorted(names)

    def generate(self, prompt: str, want_json: bool = False, model: str = None) -> str:
        """Send one prompt and return the text reply. `model` overrides the main model for one call."""
        if self.calls_made >= self.max_calls:
            raise CallLimitReached(f"Reached the cap of {self.max_calls} model calls for this run.")
        self.calls_made += 1

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=0.4,
            response_mime_type="application/json" if want_json else "text/plain",
        )
        first = model or self.model_name
        models = [first] + ([self.fallback_model] if self.fallback_model and self.fallback_model != first else [])
        last_problem = ""
        for model in models:
            started = time.monotonic()
            try:
                response = self._client.models.generate_content(model=model, contents=prompt, config=config)
            except Exception as error:  # noqa: BLE001
                message = str(error)
                if _is_server_side(error, message):
                    last_problem = message[:200]
                    print(f"  ({model} failed on Google's side after {time.monotonic() - started:.0f}s: "
                          f"{last_problem.split('.')[0]})")
                    continue  # try the fallback model
                if "429" in message or "RESOURCE_EXHAUSTED" in message:
                    raise SystemExit("Gemini free-tier limit reached. Try again later.") from error
                if "404" in message or "not found" in message.lower():
                    raise SystemExit(
                        f"Model '{model}' isn't available on your key. "
                        "Run `python -m agent.main --list-models` and put one of the listed names "
                        f"in config.yaml.\nDetails: {message[:300]}"
                    ) from error
                raise
            if model != first:
                print(f"  (answered by fallback model {model})")
            print(f"  (model answered in {time.monotonic() - started:.0f}s)")
            return response.text or ""

        raise SystemExit(
            "Google's servers couldn't complete the request on any configured model. This is usually "
            "temporary on the free tier, so try again in a few minutes.\n"
            f"Details: {last_problem}"
        )
