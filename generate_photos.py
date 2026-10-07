"""
Optional: generate photo-realistic menu images with Google's Nano Banana image models.

    pip install google-genai
    export GEMINI_API_KEY=your-key        (Windows PowerShell:  $env:GEMINI_API_KEY="your-key")
    python generate_photos.py            # all 20 items
    python generate_photos.py latte mocha  # just these

Images are saved as images/<id>.png and the app picks them up automatically.
Note: image models may not be included in the free API tier for every account. If you get a
quota/billing error, paste the prompts from image_prompts.md into the free Gemini app instead.
"""
import json
import os
import sys
import time

from google import genai
from google.genai import errors, types

MODELS = [os.environ.get("GEMINI_IMAGE_MODEL"), "gemini-3.1-flash-lite-image", "gemini-nano-banana-2.1",
          "gemini-3.1-flash-image", "gemini-2.5-flash-image"]
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("Set GEMINI_API_KEY first.")
    client = genai.Client(api_key=key)
    spec = json.load(open(os.path.join(HERE, "image_prompts.json"), encoding="utf-8"))
    wanted = sys.argv[1:] or list(spec["subjects"])
    models = [m for m in MODELS if m]

    for item_id in wanted:
        prompt = f"{spec['style']} Subject: {spec['subjects'][item_id]}."
        for model in list(models):
            try:
                resp = client.models.generate_content(
                    model=model, contents=prompt,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"]))
                parts = [p for p in resp.candidates[0].content.parts if p.inline_data]
                if not parts:
                    print(f"{item_id}: no image returned by {model}")
                    break
                path = os.path.join(HERE, "images", f"{item_id}.png")
                with open(path, "wb") as f:
                    f.write(parts[0].inline_data.data)
                print(f"{item_id}: saved {path} ({model})")
                models = [model] + [m for m in models if m != model]  # stick with the one that works
                break
            except errors.APIError as e:
                if e.code == 404:
                    models.remove(model)
                    continue
                print(f"{item_id}: {model} failed ({e.code}): {e.message}")
                break
        time.sleep(4)  # stay under free-tier per-minute limits


if __name__ == "__main__":
    main()
