"""Model wrapper. The rest of the agent only calls `generate`, so the provider can be swapped
in config.yaml without changing the agent's logic (US-7.2)."""

import os


class CallLimitReached(RuntimeError):
    pass


class LLM:
    def __init__(self, model_config: dict):
        self.provider = model_config["provider"]
        self.model_name = model_config["name"]
        self.max_calls = model_config.get("max_calls_per_run", 5)
        self.calls_made = 0

        api_key = os.environ.get(model_config["api_key_env"])
        if not api_key:
            raise SystemExit(
                f"No API key found. Add a secret called {model_config['api_key_env']} "
                "in your repo's Codespaces settings, then rebuild or restart the codespace."
            )

        if self.provider == "gemini":
            from google import genai

            self._client = genai.Client(api_key=api_key)
        else:
            raise SystemExit(f"Provider '{self.provider}' is not supported yet.")

    def generate(self, prompt: str, want_json: bool = False) -> str:
        """Send one prompt to the model and return its text reply."""
        if self.calls_made >= self.max_calls:
            raise CallLimitReached(f"Reached the cap of {self.max_calls} model calls for this run.")
        self.calls_made += 1

        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=0.4,
            response_mime_type="application/json" if want_json else "text/plain",
        )
        try:
            response = self._client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )
        except Exception as error:  # noqa: BLE001
            message = str(error)
            if "429" in message or "RESOURCE_EXHAUSTED" in message:
                raise SystemExit("Gemini free-tier limit reached. Try again later.") from error
            if "404" in message or "not found" in message.lower():
                raise SystemExit(
                    f"Model '{self.model_name}' isn't available on your key. "
                    "Change model.name in config.yaml to a model listed in Google AI Studio."
                ) from error
            raise
        return response.text or ""
