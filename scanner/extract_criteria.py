#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import random
import spacy
from spacy.training import Example
from spacy.scorer import Scorer

# ----------------------------
# Configuration
# ----------------------------
OUTPUT_MODEL = "trained_transfer_model"

# ----------------------------
# Utility: Load Doccano JSONL
# ----------------------------

def load_doccano(fname):
    """
    Reads a Doccano JSONL file and returns
    a list of (text, {'entities': [(start, end, label), ...]})
    Supports 'spans', 'labels', 'label', and 'entities' fields.
    """
    if not os.path.isfile(fname):
        raise FileNotFoundError(f"Annotation file not found: {fname}")
    data = []
    with open(fname, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            text = obj.get('text', '')
            raw_spans = []
            # Doccano exports may use any of these keys:
            raw_spans.extend(obj.get('spans', []))
            raw_spans.extend(obj.get('labels', []))
            raw_spans.extend(obj.get('label', []))
            raw_spans.extend(obj.get('entities', []))

            ents = []
            for span in raw_spans:
                if isinstance(span, dict):
                    start = span.get('start_offset') or span.get('start')
                    end = span.get('end_offset') or span.get('end')
                    label = span.get('label')
                elif isinstance(span, (list, tuple)) and len(span) >= 3:
                    start, end, label = span[0], span[1], span[2]
                else:
                    continue
                ents.append((start, end, label))

            data.append((text, {'entities': ents}))
    return data

# ----------------------------
# Utility: Extract unique labels from annotations
# ----------------------------

def get_labels(data):
    labels = set()
    for _, ann in data:
        for _, _, lbl in ann['entities']:
            labels.add(lbl)
    return list(labels)

# ----------------------------
# Training function
# ----------------------------

def train_spacy(train_data, dev_data, n_iter=20):
    # DEBUG: Print how many examples and labels we loaded
    print(f"Loaded {len(train_data)} training examples; {len(dev_data)} dev examples.")
    labels = get_labels(train_data)
    print("Labels extracted from training data:", labels)

    nlp = spacy.blank("en")
    ner = nlp.add_pipe('ner', last=True)
    for label in labels:
        ner.add_label(label)

    optimizer = nlp.initialize()
    for itn in range(n_iter):
        random.shuffle(train_data)
        losses = {}
        for text, ann in train_data:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, ann)
            nlp.update([example], sgd=optimizer, drop=0.2, losses=losses)
        print(f"Iteration {itn+1}/{n_iter} - Losses: {losses}")

    os.makedirs(OUTPUT_MODEL, exist_ok=True)
    nlp.to_disk(OUTPUT_MODEL)
    print(f"Saved model to {OUTPUT_MODEL}")

    scorer = Scorer()
    eval_nlp = spacy.load(OUTPUT_MODEL)
    examples = []
    for text, ann in dev_data:
        doc = eval_nlp(text)
        examples.append(Example.from_dict(doc, ann))
    dev_scores = scorer.score(examples)
    print("Dev set scores:", dev_scores)

# ----------------------------
# Extraction function
# ----------------------------

def extract_entities(text, nlp):
    doc = nlp(text)
    return [(ent.label_, ent.text) for ent in doc.ents]

# ----------------------------
# CLI entrypoint
# ----------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_criteria.py train <train.jsonl> <dev.jsonl>")
        print("  python extract_criteria.py extract <agreements.json(.jsonl)>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode == 'train':
        if len(sys.argv) != 4:
            print("Provide both train and dev JSONL files:")
            print("  python extract_criteria.py train <train.jsonl> <dev.jsonl>")
            sys.exit(1)
        train_file, dev_file = sys.argv[2], sys.argv[3]
        train_data = load_doccano(train_file)
        dev_data = load_doccano(dev_file)
        train_spacy(train_data, dev_data)
    elif mode == 'extract':
        if len(sys.argv) != 3:
            print("Provide the agreements file:")
            print("  python extract_criteria.py extract <agreements.json(.jsonl)>")
            sys.exit(1)
        input_path = sys.argv[2]
        docs = load_docs(input_path) if input_path.lower().endswith('.jsonl') else []
        nlp = spacy.load(OUTPUT_MODEL)
        for rec in docs:
            ents = extract_entities(rec['text'], nlp)
            print(f"\n--- Document ID: {rec.get('id','N/A')} ---")
            for lbl, txt in ents:
                print(f"{lbl}: {txt}")
    else:
        print(f"Unknown mode '{mode}'")
