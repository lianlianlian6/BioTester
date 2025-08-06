import os
import json
import torch
from tqdm import tqdm
from transformers import RobertaTokenizer, RobertaModel
import numpy as np
from scipy.spatial.distance import cosine

MODEL_NAME = "your_path/codet5-base"
JSON_PATH = "./process/program.json"

tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
model = RobertaModel.from_pretrained(MODEL_NAME, local_files_only=True)
model.eval()
model.cuda() 

def get_code_embedding(code):
    inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.cuda() for k, v in inputs.items()} 
    with torch.no_grad():
        outputs = model(**inputs)
        # embedding = outputs.last_hidden_state[:, 0, :]  # shape: (1, hidden_size)
        embedding_mean = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        return embedding_mean #embedding.squeeze(0).cpu().numpy()

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1).flatten()
    vec2 = np.array(vec2).flatten()
    cosine_sim = 1 - cosine(vec1, vec2) 
    return cosine_sim

def main():
    if not os.path.exists(JSON_PATH):
        print(f"[Error] File not found: {JSON_PATH}")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in tqdm(data, desc="Computing CodeT5 similarity"):
        code = entry.get("test_program", "")
        gen = entry.get("generation", "")
        if code.strip() and gen.strip():
            try:
                vec1 = get_code_embedding(code)
                vec2 = get_code_embedding(gen)
                similarity = cosine_similarity(vec1, vec2)
                entry["similarity"] = float(round(similarity, 4))
            except Exception as e:
                print(f"[!] Error computing similarity: {e}")
                entry["similarity"] = None
        else:
            entry["similarity"] = None

    out_PATH = "./process/program1.json"
    with open(out_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Code embedding similarity computation complete.")

if __name__ == "__main__":
    main()

