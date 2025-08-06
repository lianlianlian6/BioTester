import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm
import csv
import ast
from peft import PeftModel
import re

# === 默认路径配置 ===
BASE_MODEL = '/root/autodl-tmp/code_summarize_20250222/DeepSeek-R1-Distill-Llama-8B'
ADAPTER_PATH = '/root/autodl-tmp/code_summarize_20250222/output/0415'
INPUT_PATH = './process/program.json'
KG_PATH = './process/knowledge_database.csv'
OUTPUT_PATH = INPUT_PATH  # 可改为 './process/program_with_intention.json' 以保留原始文件

# === 加载模型和 tokenizer ===
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, local_files_only=True)
base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, local_files_only=True)
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH, local_files_only=True)
model = model.merge_and_unload()
model.eval()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def generate_intention(code, max_new_tokens=128):
    """
    使用模型为函数代码生成意图摘要
    """
    prompt = f"Please summarize the intent of the given code as concisely as possible: {code}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(device)
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]
    with torch.no_grad():
        outputs = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            top_p=0.95,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
    generated_ids = outputs[0][input_ids.shape[1]:]
    decoded = tokenizer.decode(generated_ids, skip_special_tokens=True)
    return decoded.strip()

def extract_func_name(code_snippet):
    """
    Extract the first top-level function name from a given code snippet.
    """
    try:
        tree = ast.parse(code_snippet)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                return node.name
    except Exception as e:
        print(f"[Warning] Failed to extract function name: {e}")
    return None

def main():
    if not os.path.exists(INPUT_PATH):
        print(f"[Error] Input file does not exist: {INPUT_PATH}")
        return

    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    knowledge_triples = []

    for entry in tqdm(data, desc="Generating function intentions"):
        code = entry.get("test_program", "")
        intention = generate_intention(code)
        entry["intention"] = intention
        func_name = extract_func_name(code)
        if func_name and intention:
            knowledge_triples.append((func_name, "aims", re.sub(r"\s+", " ", intention.strip())))

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    with open(KG_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for triple in knowledge_triples:
            writer.writerow(triple)

    print(f"[✓] All function intentions generated and saved to: {OUTPUT_PATH}")
    print(f"[✓] Appended {len(knowledge_triples)} intention triples to: {KG_PATH}")


if __name__ == '__main__':
    main()
