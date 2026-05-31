"""
generate_training_data.py
--------------------------
Uses Groq's free API (Llama 3.3 70B) to generate synthetic training examples
for all 3 misinformation categories. The output CSV can be merged into the
training set via data_preprocessing.py --synthetic.

Get a free Groq API key at: https://console.groq.com
(Free tier: 14,400 requests/day, 500,000 tokens/minute)

Usage:
  python src/generate_training_data.py --api-key YOUR_KEY
  python src/generate_training_data.py --api-key YOUR_KEY --per-class 150
  python src/generate_training_data.py  # reads GROQ_API_KEY from env

Full pipeline to retrain with synthetic data:
  1. python src/generate_training_data.py --api-key YOUR_KEY --per-class 200
  2. python src/data_preprocessing.py --synthetic src/synthetic_data.csv
  3. python src/train_model.py
"""

import argparse
import os
import time

import pandas as pd

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


# ---------------------------------------------------------------------------
# Prompts for each class — tuned to produce realistic, diverse examples
# ---------------------------------------------------------------------------

LABEL_CONFIGS = {
    0: {
        "name": "Highly Deceptive",
        "description": "Conspiracy theories, cover-up claims, fabricated events, suppressed evidence, dangerous health misinformation",
        "prompt": (
            "You are generating training data for a misinformation detection AI.\n\n"
            "Generate exactly {n} examples of HIGHLY DECEPTIVE misinformation. "
            "Each example should be 2-4 sentences that reads like a real social media post or viral message. "
            "Use language like: cover-up, leaked document, whistleblower reveals, big pharma is hiding, "
            "deep state, false flag, crisis actors, suppressed cure, they don't want you to know, "
            "government is concealing, secret study was banned, fabricated by the cabal, "
            "microchips in vaccines, 5G mind control, stolen election, crisis actors, "
            "QAnon terminology, flat earth claims, moon landing hoax, adrenochrome.\n\n"
            "Topics to cover (vary them): health conspiracies, pharmaceutical cover-ups, "
            "vaccine misinformation, government surveillance, election fabrication, "
            "COVID hoaxes, 5G conspiracies, suppressed cancer cures, chemtrails, "
            "climate change denial conspiracies, antisemitic cabal narratives.\n\n"
            "Make these sound urgent and emotionally charged — real conspiracy content always does.\n\n"
            "Output ONLY the {n} examples, one per line. No numbering. No extra commentary."
        ),
    },
    1: {
        "name": "Misleading",
        "description": "Exaggerated stats, vague citations, unnamed sources, sensationalist language, misleading framing of real events",
        "prompt": (
            "You are generating training data for a misinformation detection AI.\n\n"
            "Generate exactly {n} examples of MISLEADING content. "
            "These should be plausible-sounding but contain problems like: "
            "suspiciously precise statistics without a named source (e.g. '73% improvement'), "
            "anonymous or unnamed sources ('experts say', 'according to insiders'), "
            "sensationalist words (bombshell, shocking truth, explosive reveal, stunning), "
            "guaranteed or absolute claims ('100% proven', 'completely confirmed'), "
            "real events given a misleading spin or missing key context, "
            "selectively cherry-picked data that distorts the overall picture, "
            "or quotes from real people taken wildly out of context.\n\n"
            "These should NOT use full conspiracy language (no deep state, no microchips) — "
            "they should seem like questionable but plausible news articles or social posts.\n\n"
            "Topics: health supplements, AI and jobs, cryptocurrency claims, "
            "climate statistics, diet trends, economic forecasts, political polling, "
            "tech industry predictions, pharmaceutical side effects.\n\n"
            "Output ONLY the {n} examples, one per line. No numbering. No extra commentary."
        ),
    },
    2: {
        "name": "Legitimate",
        "description": "Credible, well-sourced, factual reporting with balanced language and named sources",
        "prompt": (
            "You are generating training data for a misinformation detection AI.\n\n"
            "Generate exactly {n} examples of LEGITIMATE, credible news or factual content. "
            "Each example should be 2-3 sentences that reads like genuine, well-sourced journalism "
            "or an official factual statement. "
            "Use: specific named sources (e.g. 'The WHO', 'the Federal Reserve', "
            "'according to a study published in The Lancet', 'the Justice Department announced'), "
            "balanced and measured language, verifiable facts, realistic and specific statistics "
            "with proper attribution, and neutral framing that presents multiple perspectives where relevant. "
            "NO sensationalism, NO unnamed sources, NO conspiracy language, NO misleading framing, "
            "NO guaranteed claims.\n\n"
            "Topics to cover (vary them): international news events, peer-reviewed science, "
            "economic data releases, public health updates from official bodies, "
            "political events stated factually, technology developments with sourced claims, "
            "environmental findings from credible research institutions, "
            "legal proceedings and court outcomes.\n\n"
            "These should be the kind of content you would find in Reuters, AP, BBC, or The Guardian — "
            "factual, attributed, and balanced.\n\n"
            "Output ONLY the {n} examples, one per line. No numbering. No extra commentary."
        ),
    },
}


def generate_batch(client, label: int, n: int, model: str) -> list:
    """Call Groq API and return a list of generated text examples."""
    cfg    = LABEL_CONFIGS[label]
    prompt = cfg["prompt"].format(n=n)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=n * 130,
        )
        raw   = response.choices[0].message.content.strip()
        lines = [l.strip() for l in raw.split("\n") if len(l.strip()) > 40]
        # Strip any accidental numbering (e.g. "1. ", "- ")
        cleaned = []
        for line in lines:
            if line[:3] in ("1. ", "2. ", "3. ") or line.startswith("- "):
                line = line.split(" ", 1)[-1].strip()
            cleaned.append(line)
        return cleaned[:n]
    except Exception as e:
        print(f"    [ERROR] {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic misinformation training data using Groq (free)"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("GROQ_API_KEY"),
        help="Groq API key. Get one free at https://console.groq.com  (or set GROQ_API_KEY env var)",
    )
    parser.add_argument(
        "--per-class",
        type=int,
        default=50,
        help="Number of examples to generate per class (default: 50, max recommended: 300)",
    )
    parser.add_argument(
        "--model",
        default="llama-3.3-70b-versatile",
        help="Groq model to use (default: llama-3.3-70b-versatile)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Examples per API call — smaller = more reliable (default: 25)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output CSV path (default: src/synthetic_data.csv)",
    )
    args = parser.parse_args()

    if not HAS_GROQ:
        print("[ERROR] groq package not installed.")
        print("        Run: pip install groq")
        return

    if not args.api_key:
        print("[ERROR] No Groq API key provided.")
        print("        Get a free key at: https://console.groq.com")
        print("        Then run: python src/generate_training_data.py --api-key YOUR_KEY")
        return

    output_path = args.out or os.path.join(os.path.dirname(__file__), "synthetic_data.csv")

    # Load existing synthetic data so we can append rather than overwrite
    existing_rows = []
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path)
            existing_rows = existing_df.to_dict("records")
            print(f"Appending to existing file ({len(existing_rows)} rows already present).")
        except Exception:
            pass

    client   = Groq(api_key=args.api_key)
    new_rows = []

    for label, cfg in LABEL_CONFIGS.items():
        print(f"\n[{cfg['name']}] Generating {args.per_class} examples...")
        collected = []
        remaining = args.per_class

        while remaining > 0:
            batch_n = min(args.batch_size, remaining)
            print(f"  Requesting {batch_n} examples...", end=" ", flush=True)
            batch = generate_batch(client, label, batch_n, args.model)
            print(f"got {len(batch)}")
            collected.extend(batch)
            remaining -= len(batch)
            if len(batch) < batch_n:
                # API returned fewer than asked — stop to avoid infinite loop
                break
            if remaining > 0:
                time.sleep(0.5)  # polite pause for free tier rate limits

        print(f"  Total collected: {len(collected)}")
        for text in collected:
            new_rows.append({"text": text, "label": label})

    # Merge with existing, deduplicate, save
    all_rows = existing_rows + new_rows
    df = pd.DataFrame(all_rows)
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)
    df.to_csv(output_path, index=False)

    print(f"\n{'─' * 50}")
    print(f"Synthetic dataset: {len(df)} total examples")
    print("Label distribution:")
    for lbl, cfg in LABEL_CONFIGS.items():
        count = (df["label"] == lbl).sum()
        print(f"  {lbl} ({cfg['name']}): {count}")

    print(f"\nSaved to: {output_path}")
    print("\nNext steps to retrain with this data:")
    print(f"  python src/data_preprocessing.py --synthetic {output_path}")
    print("  python src/train_model.py")


if __name__ == "__main__":
    main()
