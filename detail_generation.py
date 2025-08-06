import openai
import json
import os
from tqdm import tqdm
import time
import concurrent.futures
import re
import csv

openai.api_key = 'your_api_key'

def extract_function_name(code):
    match = re.search(r'def\s+([a-zA-Z_]\w*)\s*\(', code)
    return match.group(1) if match else None

def load_knowledge_graph(kg_path):
    call_map = {}
    with open(kg_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['relation'] == 'calls':
                caller = row['caller']
                callee = row['callee']
                call_map.setdefault(caller, set()).add(callee)
    return call_map

def build_funcname_to_text_map(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        program_data = json.load(f)

    fn2text = {}
    for entry in program_data:
        fn = extract_function_name(entry.get("test_program", ""))
        if fn:
            fn2text[fn] = entry.get("text", [])
    return fn2text

def collect_related_text(code):
    fn = extract_function_name(code)
    results = []

    if fn and fn in call_map:
        for callee in call_map[fn]:
            if callee in fn2text:
                results.append({
                    "function": callee,
                    "text": fn2text[callee]
                })
    return results

def find_most_relevant_text(code, intention, rag_texts, related_information, retries=5, delay=5):
    formatted_related_info = "\n".join(
        f"Function: {item['function']}\nText: {item['text']}" for item in related_information
    )
    for attempt in range(retries):
        try:
            prompt = (
                "Given the following code snippet and its intended purpose, your task is to extract the most relevant background information "
                "from the provided reference texts to help interpret how the code is implemented.\n\n"
                f"Code snippet:\n{code}\n\n"
                f"Intention:\n{intention}\n\n"
                f"Reference texts:\n{rag_texts}\n\n"
                "And this code calls the following functions, and their related texts are also given for reference:\n"
                f"{formatted_related_info}\n\n"
                "Your response should:\n"
                "1. Identify the most relevant parts of the reference texts that can aid in understanding the code's implementation details.\n"
                "2. Provide a concise but complete explanation of the background knowledge needed to comprehend the algorithm.\n"
                "3. According to the reference information, determine whether there are bugs in the code snippet and keep the logic of correct parts.\n"
                "4. Summarize the complete algorithm logic based primarily on the reference text correctly to support potential code reimplementation.\n\n"
                "Only return the summary text without any formatting or commentary."
            )

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            return response["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print("All retries failed for a code snippet.")
                return ""

def process_single_supple(idx_program):
    idx, program = idx_program
    code = program.get("test_program", "")
    intention = program.get("intention", "")
    text = program.get("text", "")
    related_information = collect_related_text(code)
    supplementary = find_most_relevant_text(code, intention, text, related_information)
    program["supplementary"] = supplementary
    time.sleep(1)
    return idx, program

def process_json_add_supple(input_json, output_json, num_entries=None, max_workers=5):
    with open(input_json, 'r', encoding='utf-8') as f:
        programs = json.load(f)

    filtered_programs = [(idx, programs[idx]) for idx in range(len(programs))]

    if num_entries is not None:
        selected_programs = filtered_programs[:min(num_entries, len(filtered_programs))]
    else:
        selected_programs = filtered_programs

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = list(tqdm(executor.map(process_single_supple, selected_programs),
                            total=len(selected_programs),
                            desc="Supplementing descriptions"))

    for idx, updated_program in futures:
        programs[idx] = updated_program

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(programs, f, ensure_ascii=False, indent=2)

def generate_description(supplementary, retries=5, delay=5):
    prompt = (
        "You are an expert in algorithm design.\n\n"
        "Your task is to write correct and complete algorithm pseudocode based solely on the provided description.\n\n"
        "Instructions:\n"
        "1. Read and understand the supplementary explanation carefully.\n"
        "2. Write pseudocode that fully implements the described logic.\n"
        "3. Do NOT include any explanations, comments, or markdown formatting like ```python.\n"
        "4. Output ONLY the pseudocode, as plain text.\n\n"
        "Description:\n"
        f"{supplementary}"
    )

    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional technical writer skilled in explaining algorithms."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print("All retries failed for a program.")
                return ""

def process_single_description(idx_program):
    idx, program = idx_program
    supplementary = program.get("supplementary", "")
    if supplementary:
        description = generate_description(supplementary)
        program["description"] = description
        time.sleep(1)
    return idx, program

def process_json_add_description(input_json, output_json, num_entries=None, max_workers=5):
    with open(input_json, 'r', encoding='utf-8') as f:
        programs = json.load(f)

    filtered_programs = [(idx, programs[idx]) for idx in range(len(programs))]

    if num_entries is not None:
        selected_programs = filtered_programs[:min(num_entries, len(filtered_programs))]
    else:
        selected_programs = filtered_programs

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = list(tqdm(executor.map(process_single_description, selected_programs),
                            total=len(selected_programs),
                            desc="Generating descriptions"))

    for idx, updated_program in futures:
        programs[idx] = updated_program

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(programs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    input_json = "./process/program.json"
    output_json = "./process/program.json"
    KG_PATH = './process/knowledge_database.csv'

    call_map = load_knowledge_graph(KG_PATH)
    fn2text = build_funcname_to_text_map(input_json)
    print("🔍 Starting background knowledge supplementation...")
    process_json_add_supple(input_json, output_json, num_entries=None, max_workers=5)

    print("🧠 Starting pseudocode generation...")
    process_json_add_description(input_json, output_json, num_entries=None, max_workers=5)

    print("✅ Detail generation completed.")

