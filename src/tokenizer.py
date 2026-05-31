import os
import warnings

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")

from transformers import DistilBertTokenizer

# FIX 1: tokenizer.py was loading from "distilbert-base-uncased" (downloads fresh each time)
# but predict.py loads from "models/" (the saved fine-tuned tokenizer).
# These MUST be the same tokenizer — so always load from models/ if it exists,
# fall back to distilbert-base-uncased only if models/ isn't ready yet.
TOKENIZER_PATH = "models/" if os.path.exists("models/tokenizer_config.json") else "distilbert-base-uncased"
tokenizer = DistilBertTokenizer.from_pretrained(TOKENIZER_PATH)
print(f"Tokenizer loaded from: {TOKENIZER_PATH}")

def tokenize_data(texts):
    # FIX 2: Added input type guard — passing a single string instead of a list
    # caused silent shape errors in older versions of transformers
    if isinstance(texts, str):
        texts = [texts]

    tokens = tokenizer(
        list(texts),
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt"
    )

    return tokens


if __name__ == "__main__":
    sample_texts = [
        "Vaccines cause infertility",
        "Scientists confirm the earth is flat",
        "New study shows moderate exercise improves health"
    ]

    tokens = tokenize_data(sample_texts)

    # FIX 3: Print useful debug info instead of just the raw tensor
    print(f"Number of samples tokenized : {len(sample_texts)}")
    print(f"input_ids shape             : {tokens['input_ids'].shape}")
    print(f"attention_mask shape        : {tokens['attention_mask'].shape}")
