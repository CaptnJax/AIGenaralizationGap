"""Local CPU/CUDA VulBERTa evaluation; invoked by pivd_local.py."""
import os
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ["USE_TF"] = "0"

import argparse
import hashlib
import json
import faulthandler
import re
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer, set_seed

PREPROCESSING_VERSION = "original_vulberta_cleaner_v1"


def clean_for_vulberta(code):
    """Match cleaner() in the authors' Evaluation_VulBERTa-MLP.ipynb.

    Apply before Clang receives the text. The converted tokenizer's serialized
    Replace pattern is literal, and its Clang callback reads original text.
    This deliberately reproduces the authors' regex, including its limitations
    around comment-like text inside string literals; it is not a C/C++ parser.
    """
    code = re.sub(r'(/\*([^*]|(\*+[^*/]))*\*+/)|(//.*)', '', code)
    return code.replace('\n', '').replace('\t', '')


def fix_clang_parser(tokenizer):
    """Keep Clang's lexical tokens while bypassing function-body parsing hangs."""
    from clang import cindex
    from tokenizers import NormalizedString
    from tokenizers.pre_tokenizers import PreTokenizer

    class ClangPreTokenizer:
        cidx = cindex.Index.create()

        def clang_split(self, i, normalized_string):
            tu = self.cidx.parse(
                "tmp.c", args=[""],
                unsaved_files=[("tmp.c", str(normalized_string.original))],
                options=cindex.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES,
            )
            tokens = []
            for token in tu.get_tokens(extent=tu.cursor.extent):
                spelling = token.spelling.strip()
                if spelling:
                    tokens.append(NormalizedString(spelling))
            return tokens

        def pre_tokenize(self, pretok):
            pretok.split(self.clang_split)

    tokenizer._tokenizer.pre_tokenizer = PreTokenizer.custom(ClangPreTokenizer())


def save_progress(path, signature, scores):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"signature": signature, "scores": scores}), encoding="utf-8")
    os.replace(temporary, path)


def load_progress(path, signature, rows):
    state = json.loads(path.read_text(encoding="utf-8"))
    if state["signature"] != signature:
        raise ValueError("Saved progress uses different data/settings. Use a new --output_dir.")
    scores = state["scores"]
    if len(scores) > rows or any(not isinstance(x, (float, int)) or not 0 <= x <= 1 for x in scores):
        raise ValueError("Invalid saved progress.")
    if len(scores) != rows and len(scores) % signature["batch_size"]:
        raise ValueError("Saved progress ends inside a batch.")
    return scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", default="claudios/VulBERTa-MLP-Devign")
    parser.add_argument("--revision", default="fecabdee24a3ef6e804d7629d6eed03dc6b4f61e")
    parser.add_argument("--test_data_file", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, default=Path(__file__).resolve().parent / "results" / "vulberta")
    parser.add_argument("--block_size", type=int, default=1024)
    parser.add_argument("--eval_batch_size", type=int, default=16)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true", help="Reuse completed batches with identical settings.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()
    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable. Use --device cpu or install CUDA-enabled PyTorch.")
    if args.block_size < 2 or args.eval_batch_size < 1 or not 0 <= args.threshold <= 1:
        raise ValueError("Invalid block size, batch size, or threshold.")
    set_seed(args.seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    df = pd.read_csv(args.test_data_file, keep_default_na=False)
    required = {"sample_id", "func", "label"}
    if not required.issubset(df.columns) or df.empty:
        raise ValueError("Expected a nonempty prepared VulBERTa CSV: sample_id, func, label.")
    if not df.label.isin([0, 1]).all() or not df.sample_id.is_unique or df.func.str.strip().eq("").any():
        raise ValueError("Invalid labels, duplicate sample IDs, or empty functions.")
    print(f"device: {device}; GPU: {torch.cuda.get_device_name(0) if device == 'cuda' else 'none'}", flush=True)
    print(f"Dataset: {args.test_data_file}; rows: {len(df)}", flush=True)
    print(f"Label counts: {df.label.value_counts().to_dict()}", flush=True)
    print(f"Checkpoint: {args.model_name_or_path}@{args.revision}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(
        args.model_name_or_path, revision=args.revision, trust_remote_code=True,
    )
    fix_clang_parser(tokenizer)
    model, loading = AutoModelForSequenceClassification.from_pretrained(
        args.model_name_or_path, revision=args.revision,
        use_safetensors=True, output_loading_info=True,
    )
    problems = {k: loading.get(k) for k in
                ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs") if loading.get(k)}
    if problems:
        raise RuntimeError(f"Checkpoint did not load cleanly: {problems}")
    if model.config.num_labels != 2:
        raise ValueError("Expected a binary classification checkpoint.")
    max_length = model.config.max_position_embeddings - model.config.pad_token_id - 1
    if args.block_size > max_length:
        raise ValueError(f"block_size exceeds this checkpoint's limit of {max_length}.")
    model.to(device).eval()
    print("Trained classifier loaded successfully. Starting test.", flush=True)

    output = args.output_dir / args.test_data_file.stem
    output.mkdir(parents=True, exist_ok=True)
    signature = {
        "model": args.model_name_or_path, "revision": args.revision,
        "dataset_sha256": hashlib.sha256(args.test_data_file.read_bytes()).hexdigest(),
        "block_size": args.block_size, "batch_size": args.eval_batch_size, "seed": args.seed,
        "tokenizer_fix": "clang_skip_function_bodies_v1", "device": device,
        "preprocessing": PREPROCESSING_VERSION,
        "versions": {p: version(p) for p in ("torch", "transformers", "tokenizers", "libclang")},
    }
    progress_path = output / "progress.json"
    scores = load_progress(progress_path, signature, len(df)) if args.resume and progress_path.exists() else []
    print(f"Completed rows restored: {len(scores)}", flush=True)
    print("Clang parser fix enabled; completed batches will be saved.", flush=True)
    print(f"Preprocessing: {PREPROCESSING_VERSION} (comments, newlines and tabs removed before tokenization).", flush=True)
    starts = range(len(scores), len(df), args.eval_batch_size)
    faulthandler.enable()
    # A future native-library stall will show which operation is active.
    faulthandler.dump_traceback_later(120, repeat=True)
    with torch.inference_mode():
        for start in tqdm(starts, total=(len(df) + args.eval_batch_size - 1) // args.eval_batch_size,
                          initial=(len(scores) + args.eval_batch_size - 1) // args.eval_batch_size,
                          desc="VulBERTa test", unit="batch", mininterval=2):
            status = {"stage": "tokenization", "start_row_zero_based": start,
                      "sample_ids": df.sample_id.iloc[start:start + args.eval_batch_size].tolist()}
            (output / "current_batch.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
            funcs = [clean_for_vulberta(code)
                     for code in df.func.iloc[start:start + args.eval_batch_size]]
            encoded = tokenizer(
                funcs, padding="max_length", truncation=True,
                max_length=args.block_size, return_tensors="pt",
                return_token_type_ids=False,
            )
            status["stage"] = f"{device} inference"
            (output / "current_batch.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
            inputs = {k: encoded[k].to(device) for k in ("input_ids", "attention_mask")}
            probabilities = model(**inputs).logits.softmax(dim=-1)[:, 1]
            batch_scores = probabilities.cpu().tolist()
            if not np.isfinite(batch_scores).all():
                raise RuntimeError("Non-finite prediction probabilities encountered.")
            scores.extend(batch_scores)
            save_progress(progress_path, signature, scores)
            faulthandler.dump_traceback_later(120, repeat=True)
    faulthandler.cancel_dump_traceback_later()
    (output / "current_batch.json").write_text(json.dumps({"stage": "complete", "rows": len(scores)}), encoding="utf-8")

    scores = np.asarray(scores)
    if not np.isfinite(scores).all():
        raise RuntimeError("Non-finite prediction probabilities encountered.")
    labels = df.label.to_numpy(dtype=int)
    predictions = (scores > args.threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()
    metrics = {
        "test_accuracy": float(accuracy_score(labels, predictions)),
        "test_f1": float(f1_score(labels, predictions, zero_division=0)),
        "test_precision": float(precision_score(labels, predictions, zero_division=0)),
        "test_recall": float(recall_score(labels, predictions, zero_division=0)),
        "test_threshold": args.threshold,
    }
    pd.DataFrame({"sample_id": df.sample_id, "label": labels,
                  "prob_vulnerable": scores, "prediction": predictions}).to_csv(
        output / "predictions.csv", index=False)
    report = {
        **metrics, "rows": len(df),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "model": args.model_name_or_path, "revision": args.revision,
        "tokenizer_fix": signature["tokenizer_fix"],
        "preprocessing": signature["preprocessing"],
        "dataset": str(args.test_data_file),
        "dataset_sha256": hashlib.sha256(args.test_data_file.read_bytes()).hexdigest(),
        "block_size": args.block_size, "batch_size": args.eval_batch_size, "seed": args.seed,
        "device": device, "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "versions": {p: version(p) for p in
                     ("torch", "transformers", "tokenizers", "libclang", "pandas", "scikit-learn")},
    }
    (output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n***** Test results *****", flush=True)
    for key, value in metrics.items():
        print(f"  {key} = {value:.4f}", flush=True)
    print(f"Saved metrics.json and predictions.csv to {output}", flush=True)


if __name__ == "__main__":
    main()
