"""
train_model.py
--------------
Trains a DistilBERT misinformation classifier with 3 output classes:
  0 = Highly Deceptive
  1 = Misleading
  2 = Legitimate

Improvements over the previous version:
  - Argparse — all hyperparameters are configurable from the command line
  - Uses ALL available training data by default (no arbitrary 1500-sample cap)
  - Cosine scheduler with warmup (better than linear for transformers)
  - Differential learning rates — classifier head trains 5x faster than backbone
  - Label smoothing (0.1) — reduces overconfidence and improves generalisation
  - Mixed precision training (AMP) — faster on GPU, same accuracy
  - Per-class F1 score reported after every epoch
  - Early stopping on MACRO F1 (not val loss) — better metric for imbalanced data
  - Default epochs increased to 10, patience to 4

Usage:
  python src/train_model.py                          # default settings
  python src/train_model.py --epochs 12 --patience 4
  python src/train_model.py --max-per-class 3000     # cap samples if needed
  python src/train_model.py --max-length 256         # longer context window
"""

import argparse
import os

import numpy as np
import pandas as pd
import torch
import torch.amp as amp
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import (
    DistilBertForSequenceClassification,
    DistilBertTokenizer,
    get_cosine_schedule_with_warmup,
)

LABEL_NAMES = ["Highly Deceptive", "Misleading", "Legitimate"]


class FocalLoss(torch.nn.Module):
    """
    Focal Loss — automatically down-weights well-classified (easy) examples and
    focuses learning on hard, misclassified ones.  Far superior to weighted
    CrossEntropy when class imbalance is severe (which is our case: 4–5× ratio).

    gamma=2.0 is the standard default; alpha acts as per-class weight.
    Reference: Lin et al. 2017 — "Focal Loss for Dense Object Detection"
    """
    def __init__(self, gamma: float = 2.0, weight=None, label_smoothing: float = 0.0):
        super().__init__()
        self.gamma           = gamma
        self.weight          = weight
        self.label_smoothing = label_smoothing

    def forward(self, logits, targets):
        # Standard CE (with class weights + label smoothing)
        ce = torch.nn.functional.cross_entropy(
            logits, targets,
            weight=self.weight,
            label_smoothing=self.label_smoothing,
            reduction="none",
        )
        # p_t = probability of the correct class
        pt = torch.exp(-ce)
        # Focal weight: (1 - p_t)^gamma suppresses easy examples
        focal_weight = (1.0 - pt) ** self.gamma
        return (focal_weight * ce).mean()


class TextDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids":      enc["input_ids"].squeeze(),
            "attention_mask": enc["attention_mask"].squeeze(),
            "labels":         torch.tensor(self.labels[idx], dtype=torch.long),
        }


def main():
    parser = argparse.ArgumentParser(description="Train DistilBERT misinformation classifier")
    parser.add_argument("--train-csv",       default="src/train_data.csv",           help="Path to training CSV")
    parser.add_argument("--epochs",          type=int,   default=10,                 help="Maximum training epochs")
    parser.add_argument("--batch-size",      type=int,   default=32,                 help="Batch size")
    parser.add_argument("--lr",              type=float, default=2e-5,               help="Backbone learning rate")
    parser.add_argument("--max-length",      type=int,   default=128,                help="Token sequence length (128 or 256)")
    parser.add_argument("--max-per-class",   type=int,   default=None,               help="Cap samples per class. Omit to use all data.")
    parser.add_argument("--patience",        type=int,   default=4,                  help="Early stopping patience (epochs without improvement)")
    parser.add_argument("--label-smoothing", type=float, default=0.1,               help="Label smoothing factor (0 = disabled)")
    parser.add_argument("--dropout",         type=float, default=0.4,               help="Classifier head dropout")
    parser.add_argument("--checkpoint",      default="models/best_model_checkpoint", help="Where to save the best checkpoint during training")
    parser.add_argument("--output",          default="models",                       help="Where to copy the final best model")
    parser.add_argument("--resume-from",     default=None,                           help="Resume fine-tuning from this saved checkpoint (e.g. models/best_model_checkpoint)")
    parser.add_argument("--oversample",      action="store_true",                    help="Oversample minority classes to match the majority class count")
    parser.add_argument("--no-oversample",   action="store_true",                    help="Disable auto-oversampling even when class imbalance is detected")
    parser.add_argument("--focal-loss",      action="store_true",                    help="Use Focal Loss instead of CrossEntropy (better for severe class imbalance)")
    parser.add_argument("--focal-gamma",     type=float, default=2.0,               help="Focal Loss gamma exponent (default 2.0; higher = more focus on hard examples)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda"
    print(f"Device : {device}")
    print(f"AMP    : {'enabled' if use_amp else 'disabled (CPU)'}")

    # ── Load data ──────────────────────────────────────────────────────────────
    print(f"\nLoading training data from {args.train_csv} ...")
    data = pd.read_csv(args.train_csv).dropna()
    data["text"] = data["text"].astype(str).str.strip()
    data = data[data["text"].str.len() > 10].reset_index(drop=True)

    if args.max_per_class:
        min_count = data["label"].value_counts().min()
        cap = min(min_count, args.max_per_class)
        data = data.groupby("label").sample(cap, random_state=42).reset_index(drop=True)
        print(f"Capped at {cap} samples per class.")

    data = data.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"Total samples : {len(data)}")
    print("Label distribution:")
    counts = []
    for label, name in enumerate(LABEL_NAMES):
        count = (data["label"] == label).sum()
        counts.append(count)
        print(f"  {label} ({name}): {count}")

    # Auto-enable oversampling when the minority class (Highly Deceptive, label 0)
    # is more than 2× outnumbered by the majority class.  This is the most common
    # cause of the model never predicting "Highly Deceptive".
    if args.no_oversample:
        args.oversample = False
    elif not args.oversample and max(counts) > min(counts) * 2:
        args.oversample = True
        print(
            f"\n[AUTO] Class imbalance detected (ratio {max(counts)/max(min(counts),1):.1f}×). "
            "Oversampling enabled automatically. Pass --no-oversample to disable."
        )

    # ── Train / val split BEFORE any oversampling ──────────────────────────────
    # Critical: split on the original data so val examples are never duplicates
    # of train examples. This gives honest early-stopping signals.
    train_df, val_df = train_test_split(
        data, test_size=0.1, stratify=data["label"], random_state=42
    )

    if args.oversample:
        # Oversample ONLY the training set — val stays at original distribution.
        # Target = majority class count in train, capped to avoid excessive repetition.
        from sklearn.utils import resample
        train_counts = train_df["label"].value_counts()
        target = train_counts.max()
        parts = []
        for lbl in sorted(train_df["label"].unique()):
            grp = train_df[train_df["label"] == lbl]
            if len(grp) < target:
                grp = resample(grp, replace=True, n_samples=target, random_state=42)
            parts.append(grp)
        train_df = pd.concat(parts, ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
        print(f"Oversampled training set to {target} samples per class.")

    print(f"\nTrain: {len(train_df)}  |  Val: {len(val_df)}")

    # ── Class weights ──────────────────────────────────────────────────────────
    cw = compute_class_weight(
        "balanced",
        classes=np.unique(train_df["label"].tolist()),
        y=train_df["label"].tolist(),
    )
    class_weights = torch.tensor(cw, dtype=torch.float).to(device)

    # ── Tokenizer & DataLoaders ────────────────────────────────────────────────
    base_model = args.resume_from if args.resume_from else "distilbert-base-uncased"
    tokenizer  = DistilBertTokenizer.from_pretrained(base_model)

    train_ds = TextDataset(train_df["text"].tolist(), train_df["label"].tolist(), tokenizer, args.max_length)
    val_ds   = TextDataset(val_df["text"].tolist(),   val_df["label"].tolist(),   tokenizer, args.max_length)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,  pin_memory=use_amp)
    val_loader   = DataLoader(val_ds,   batch_size=args.batch_size, shuffle=False, pin_memory=use_amp)

    # ── Model ──────────────────────────────────────────────────────────────────
    if args.resume_from:
        print(f"\nResuming from checkpoint: {args.resume_from}")
        model = DistilBertForSequenceClassification.from_pretrained(args.resume_from)
    else:
        model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased", num_labels=3
        )
    model.config.seq_classif_dropout = args.dropout
    model.classifier.dropout = torch.nn.Dropout(args.dropout)
    model.to(device)

    # Differential LR: classifier head learns 5× faster than the backbone.
    # This speeds up adaptation while keeping the pre-trained representations stable.
    backbone_params = [p for n, p in model.named_parameters() if "classifier" not in n]
    head_params     = [p for n, p in model.named_parameters() if "classifier"     in n]
    optimizer = AdamW(
        [
            {"params": backbone_params, "lr": args.lr},
            {"params": head_params,     "lr": args.lr * 5},
        ],
        weight_decay=0.01,
    )

    total_steps  = len(train_loader) * args.epochs
    warmup_steps = int(0.1 * total_steps)
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    if args.focal_loss:
        loss_fn = FocalLoss(
            gamma=args.focal_gamma,
            weight=class_weights,
            label_smoothing=args.label_smoothing,
        )
        print(f"Loss   : Focal Loss (gamma={args.focal_gamma})")
    else:
        loss_fn = torch.nn.CrossEntropyLoss(
            weight=class_weights,
            label_smoothing=args.label_smoothing,
        )
        print("Loss   : CrossEntropyLoss (weighted + label smoothing)")
    scaler = amp.GradScaler("cuda", enabled=use_amp)

    # ── Training loop ──────────────────────────────────────────────────────────
    # We track macro F1 (not val loss) for early stopping — it is a better
    # metric for 3-class imbalanced data and what we actually care about.
    best_macro_f1    = -1.0
    patience_counter = 0

    print(f"\nTraining for up to {args.epochs} epoch(s)  |  patience={args.patience}  |  label_smoothing={args.label_smoothing}")
    print("Early stopping metric: macro F1 (higher = better)\n")
    print("-" * 70)

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
            scaler.unscale_(optimizer)
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
                    outputs = model(input_ids=ids, attention_mask=mask)
                    loss    = loss_fn(outputs.logits, labels)

                val_loss += loss.item()
                preds = torch.argmax(outputs.logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        avg_val    = val_loss / len(val_loader)
        macro_f1   = f1_score(all_labels, all_preds, average="macro", zero_division=0)
        report     = classification_report(
            all_labels, all_preds, target_names=LABEL_NAMES, zero_division=0
        )

        print(f"Epoch {epoch + 1}/{args.epochs}  |  Train Loss: {avg_train:.4f}  |  Val Loss: {avg_val:.4f}  |  Macro F1: {macro_f1:.4f}")
        print(report)

        if macro_f1 > best_macro_f1:
            best_macro_f1    = macro_f1
            patience_counter = 0
            os.makedirs(args.checkpoint, exist_ok=True)
            model.save_pretrained(args.checkpoint)
            tokenizer.save_pretrained(args.checkpoint)
            print(f"  ->Best model saved  (macro F1 improved to {best_macro_f1:.4f})\n")
        else:
            patience_counter += 1
            print(f"  ->No improvement  ({patience_counter}/{args.patience})\n")
            if patience_counter >= args.patience:
                print("  Early stopping triggered.\n")
                break

    # ── Copy best checkpoint to final output directory ─────────────────────────
    final = DistilBertForSequenceClassification.from_pretrained(args.checkpoint)
    os.makedirs(args.output, exist_ok=True)
    final.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)

    print("-" * 70)
    print(f"Training complete.")
    print(f"Best macro F1 : {best_macro_f1:.4f}")
    print(f"Model saved to: {args.output}/")
    print("Restart the API server to load the updated model.")


if __name__ == "__main__":
    main()
