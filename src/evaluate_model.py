import os
import torch
import pandas as pd
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, classification_report, confusion_matrix
)

# Load test data
test_data = pd.read_csv("src/test_data.csv").dropna()

# Use all available test samples

print("Test label distribution:\n", test_data["label"].value_counts())

test_texts  = test_data["text"].tolist()
test_labels = test_data["label"].tolist()

# Resolve model directory — check newest versions first
_CANDIDATES = [
    "models/final_v6",
    "models/checkpoint_v6",
    "models/final_v5",
    "models/checkpoint_v5",
    "models/final_v4",
    "models/final_v3",
    "models/final_v2",
    "models/checkpoint_v3",
    "models/checkpoint_v2",
    "models/best_model_checkpoint",
    "models",
]
MODEL_DIR = next(
    (d for d in _CANDIDATES if os.path.exists(os.path.join(d, "config.json"))),
    None,
)
if MODEL_DIR is None:
    raise RuntimeError("No trained model found. Run train_model.py first.")

tokenizer = DistilBertTokenizer.from_pretrained(MODEL_DIR)
model     = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
model.eval()

print(f"Model loaded from: {MODEL_DIR}  (num_labels={model.config.num_labels})")

# Tokenize and predict in batches
BATCH_SIZE      = 32
all_predictions = []

for i in range(0, len(test_texts), BATCH_SIZE):
    batch_texts = test_texts[i : i + BATCH_SIZE]
    tokens = tokenizer(
        batch_texts,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt",
    )
    with torch.no_grad():
        outputs = model(
            input_ids=tokens["input_ids"],
            attention_mask=tokens["attention_mask"],
        )
    preds = torch.argmax(outputs.logits, dim=1).numpy()
    all_predictions.extend(preds.tolist())

label_names = ["Highly Deceptive", "Misleading", "Legitimate"]

accuracy  = accuracy_score(test_labels, all_predictions)
precision = precision_score(test_labels, all_predictions, average="macro", zero_division=0)
recall    = recall_score(test_labels,    all_predictions, average="macro", zero_division=0)
f1        = f1_score(test_labels,        all_predictions, average="macro", zero_division=0)

print("\n--- Overall Metrics --------------------------------------------------")
print(f"  Accuracy  : {accuracy:.4f}")
print(f"  Precision : {precision:.4f}  (macro)")
print(f"  Recall    : {recall:.4f}  (macro)")
print(f"  F1 Score  : {f1:.4f}  (macro)")

print("\n--- Per-Class Report -------------------------------------------------")
print(classification_report(test_labels, all_predictions, target_names=label_names))

print("--- Confusion Matrix -------------------------------------------------")
cm    = confusion_matrix(test_labels, all_predictions)
cm_df = pd.DataFrame(cm, index=label_names, columns=label_names)
print(cm_df)
