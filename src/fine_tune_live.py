"""
fine_tune_live.py
-----------------
Fine-tunes the existing DistilBERT checkpoint on live news merged with the
original training data.  Uses a lower learning rate (1e-5) and only 2 epochs
so the model adapts to current news without forgetting what it learned.

Key improvements:
  - Oversamples minority classes in live data so fine-tuning never worsens balance
  - Uses macro F1 (not val loss) to select the best checkpoint — ensures all three
    classes stay well-classified, not just the majority class
  - AMP (mixed precision) enabled on CUDA for faster training

Steps:
  1. Run fetch_live_news.py  →  src/live_news.csv
  2. Run this script          →  models/best_model_checkpoint updated in-place

Usage:
  python src/fine_tune_live.py
  python src/fine_tune_live.py --live-news src/live_news.csv --epochs 3
"""

import argparse
import os

import numpy as np
import pandas as pd
import torch
import torch.amp as amp
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.utils import resample
from sklearn.utils.class_weight import compute_class_weight
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    get_cosine_schedule_with_warmup,
)

# ── Paths ──────────────────────────────────────────────────────────────────────
SRC_DIR      = os.path.dirname(__file__)
ROOT_DIR     = os.path.join(SRC_DIR, "..")
# Base model: always start from the current best production model
MODEL_PATH   = os.path.join(ROOT_DIR, "models", "final_v13")
# Output: a fixed "live" slot at the top of predict.py's _CANDIDATES list
OUTPUT_PATH  = os.path.join(ROOT_DIR, "models", "final_v_live")
# Training CSV: includes sports data (do NOT use the old train_data.csv alone)
TRAIN_CSV    = os.path.join(SRC_DIR, "train_data_sports.csv")
DEFAULT_LIVE = os.path.join(SRC_DIR, "live_news.csv")

LABEL_NAMES  = ["Highly Deceptive", "Misleading", "Legitimate"]


# ── Dataset ────────────────────────────────────────────────────────────────────
class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer):
        self.texts     = texts
        self.labels    = labels
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=128,
            return_tensors="pt",
        )
        return {
            "input_ids":      enc["input_ids"].squeeze(),
            "attention_mask": enc["attention_mask"].squeeze(),
            "labels":         torch.tensor(self.labels[idx], dtype=torch.long),
        }


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-news", default=DEFAULT_LIVE,  help="Path to live_news.csv")
    parser.add_argument("--model",     default=MODEL_PATH,    help="Base model checkpoint path")
    parser.add_argument("--output",    default=OUTPUT_PATH,   help="Where to save the fine-tuned model")
    parser.add_argument("--epochs",    type=int, default=2,   help="Fine-tune epochs")
    parser.add_argument("--lr",        type=float, default=1e-5, help="Learning rate")
    parser.add_argument("--batch",     type=int, default=32,  help="Batch size")
    args = parser.parse_args()

    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda"
    print(f"Device: {device}  |  AMP: {'enabled' if use_amp else 'disabled'}")

    # ── Load base training data ────────────────────────────────────────────────
    print("\nLoading training data...")
    train_df = pd.read_csv(TRAIN_CSV).dropna()
    print(f"  Existing training samples: {len(train_df)}")
    existing_counts = {lbl: int((train_df["label"] == lbl).sum()) for lbl in [0, 1, 2]}
    print("  Existing label distribution:", existing_counts)

    if not os.path.exists(args.live_news):
        print(f"\n[ERROR] Live news file not found: {args.live_news}")
        print("  Run first:  python src/fetch_live_news.py")
        return

    # ── Load and clean live news ───────────────────────────────────────────────
    live_df = pd.read_csv(args.live_news).dropna(subset=["text", "label"])
    live_df["label"] = live_df["label"].astype(int)
    live_df = live_df[live_df["label"].isin([0, 1, 2])].reset_index(drop=True)
    print(f"\n  Live news samples (total): {len(live_df)}")

    # ── Filter to only articles not already in train_data.csv ─────────────────
    # This is the key deduplication step: once an article has been trained on
    # it should never appear in a future fine-tune run.
    existing_texts = set(train_df["text"].astype(str).tolist())
    before_filter  = len(live_df)
    live_df = live_df[~live_df["text"].astype(str).isin(existing_texts)].reset_index(drop=True)
    print(f"  Already trained: {before_filter - len(live_df)}  |  New articles: {len(live_df)}")

    if len(live_df) < 20:
        print(f"\n  Less than 20 new articles — nothing new to learn. Skipping fine-tune.")
        return

    live_counts = {lbl: int((live_df["label"] == lbl).sum()) for lbl in [0, 1, 2]}
    print("  New articles by label:", live_counts)

    # ── Balance live news before merging ──────────────────────────────────────
    # Cap each live class at 2× its existing training count (so live data doesn't
    # overwhelm existing training), then oversample minority live classes so that
    # all three labels contribute roughly equally to the fine-tuning update.
    capped_parts = []
    for lbl in [0, 1, 2]:
        grp = live_df[live_df["label"] == lbl]
        existing_count = existing_counts.get(lbl, 0)
        max_for_class  = max(existing_count * 2, 200)
        if len(grp) > max_for_class:
            grp = grp.sample(max_for_class, random_state=42)
        capped_parts.append(grp)

    live_capped = pd.concat(capped_parts, ignore_index=True)
    capped_counts = {lbl: int((live_capped["label"] == lbl).sum()) for lbl in [0, 1, 2]}

    # Oversample minority live classes to match the live majority count
    live_target = max(capped_counts.values())
    balanced_parts = []
    for lbl in [0, 1, 2]:
        grp = live_capped[live_capped["label"] == lbl]
        if len(grp) == 0:
            continue
        if len(grp) < live_target:
            grp = resample(grp, replace=True, n_samples=live_target, random_state=42)
        balanced_parts.append(grp)
    live_balanced = pd.concat(balanced_parts, ignore_index=True)
    print(f"\n  Live news after balancing ({live_target} per class): {len(live_balanced)} samples")

    # ── Merge and deduplicate ─────────────────────────────────────────────────
    combined = pd.concat(
        [train_df[["text", "label"]], live_balanced[["text", "label"]]],
        ignore_index=True,
    )
    combined["text"] = combined["text"].astype(str)
    combined = combined.drop_duplicates(subset=["text"]).reset_index(drop=True)

    print(f"\nCombined dataset: {len(combined)} samples")
    print("Label distribution:")
    for lbl, name in enumerate(LABEL_NAMES):
        print(f"  {lbl} ({name}): {(combined['label'] == lbl).sum()}")

    # ── Train / validation split ───────────────────────────────────────────────
    train_split, val_split = train_test_split(
        combined, test_size=0.1, stratify=combined["label"], random_state=42
    )

    train_texts  = train_split["text"].tolist()
    train_labels = train_split["label"].tolist()
    val_texts    = val_split["text"].tolist()
    val_labels   = val_split["label"].tolist()

    # ── Class weights ──────────────────────────────────────────────────────────
    cw = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(train_labels),
        y=train_labels,
    )
    class_weights = torch.tensor(cw, dtype=torch.float).to(device)

    # ── Tokenizer & DataLoaders ────────────────────────────────────────────────
    print(f"\nLoading tokenizer and model from: {args.model}")
    print(f"Fine-tuned model will be saved to: {args.output}")
    os.makedirs(args.output, exist_ok=True)
    tokenizer = DistilBertTokenizer.from_pretrained(args.model)

    train_ds = TextDataset(train_texts, train_labels, tokenizer)
    val_ds   = TextDataset(val_texts,   val_labels,   tokenizer)

    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True,  pin_memory=use_amp)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch, shuffle=False, pin_memory=use_amp)

    # ── Model ─────────────────────────────────────────────────────────────────
    model = DistilBertForSequenceClassification.from_pretrained(args.model)
    model.to(device)

    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    total_steps  = len(train_loader) * args.epochs
    warmup_steps = max(total_steps // 10, 1)
    scheduler    = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)
    scaler  = amp.GradScaler("cuda", enabled=use_amp)

    # ── Fine-tuning loop ───────────────────────────────────────────────────────
    # Track macro F1, not val loss — this ensures all three classes stay
    # well-classified and no single class regresses during fine-tuning.
    best_macro_f1 = -1.0
    print(f"\nFine-tuning for {args.epochs} epoch(s) at lr={args.lr} ...\n")
    print("Checkpoint metric: macro F1 (higher = better)\n")

    for epoch in range(args.epochs):
        # Train
        model.train()
        total_loss = 0
        for batch in train_loader:
            ids    = batch["input_ids"].to(device)
            mask   = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            with amp.autocast("cuda", enabled=use_amp):
                outputs = model(input_ids=ids, attention_mask=mask)
                loss    = loss_fn(outputs.logits, labels)

            scaler.scale(loss).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            optimizer.zero_grad()
            total_loss += loss.item()

        avg_train = total_loss / len(train_loader)

        # Validate
        model.eval()
        val_loss   = 0
        all_preds  = []
        all_labels = []
        with torch.no_grad():
            for batch in val_loader:
                ids    = batch["input_ids"].to(device)
                mask   = batch["attention_mask"].to(device)
                labels = batch["labels"].to(device)

                with amp.autocast("cuda", enabled=use_amp):
                    outputs  = model(input_ids=ids, attention_mask=mask)
                    loss     = loss_fn(outputs.logits, labels)

                val_loss += loss.item()
                preds = torch.argmax(outputs.logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        avg_val   = val_loss / len(val_loader)
        macro_f1  = f1_score(all_labels, all_preds, average="macro", zero_division=0)
        report    = classification_report(
            all_labels, all_preds,
            target_names=LABEL_NAMES,
            zero_division=0,
        )

        print(f"Epoch {epoch+1}/{args.epochs} | Train Loss: {avg_train:.4f} | Val Loss: {avg_val:.4f} | Macro F1: {macro_f1:.4f}")
        print(report)

        # Save on macro F1 improvement — not val loss
        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            model.save_pretrained(args.output)
            tokenizer.save_pretrained(args.output)
            print(f"  -> Checkpoint saved to {args.output} (macro F1 improved to {best_macro_f1:.4f})")

    print(f"\nDone. Best macro F1: {best_macro_f1:.4f}")
    print(f"Updated model saved to: {args.model}")

    # ── Absorb new articles into train_data.csv ────────────────────────────────
    # After training, merge the newly used live articles into the permanent
    # training set.  Next fine-tune run will skip these automatically.
    try:
        updated = pd.concat(
            [train_df[["text", "label"]], live_df[["text", "label"]]],
            ignore_index=True,
        ).drop_duplicates(subset=["text"]).reset_index(drop=True)
        updated.to_csv(TRAIN_CSV, index=False)
        print(f"  train_data.csv updated: {len(train_df)} → {len(updated)} samples")
        print("  These articles will NOT be re-used in future fine-tune runs.")
    except Exception as exc:
        print(f"  [WARN] Could not update train_data.csv: {exc}")

    print("Restart the API server for the changes to take effect.")


if __name__ == "__main__":
    main()
