import openai
import json
import os
from tqdm import tqdm
import time
import concurrent.futures
import re
import traceback
import multiprocessing

openai.api_key = 'your-api-key'

def generate_code_with_assertions(test_program, assertion, retries=5, delay=5):
    prompt = (
        "You are an expert Python programmer.\n"
        "Your task is to integrate the provided assertion into the given test program.\n"
        "Instructions:\n"
        "1. Wrap the test program into a function matching the function name in the following assertion and ensure the function parameters reflect the inputs implied by the assertion.\n"
        "2. Do NOT alter the original logic or internal behavior of the test program. If bugs exist, they should be exposed through the provided assertions rather than by modifying the code.\n"
        "3. If the test program uses print statements to display outputs:\n"
        "   -  replacing all `print(...)` calls with `return ...` to produce outputs instead.\n"
        "4. Insert the assertion as an `assert` statement with each line representing one complete test case. The assert statement for a single test case must not span multiple lines.\n"
        "5. If the test program calls any external functions, please handle them appropriately to ensure that the rewritten code can run independently.\n"
        "6. The final result must be a single, clean Python script that is immediately executable.\n"
        "7. Do NOT include any explanation, comments, or `if __name__ == '__main__'` blocks.\n"
        "8. Output ONLY a single Python code block using triple backticks (i.e., ```python ... ```).\n\n"
        f"Test Program:\n{test_program}\n\n"
        f"Assertion:\n{assertion}\n\n"
        "Output:"
    )

    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional Python developer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print("All retries failed for generating code.")
                return ""  # Return empty if all retries fail


# Function to extract the Python code from the response
def extract_python_code(text):
    match = re.search(r"```python(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return text.strip()


# Function to process each entry and generate test and correct programs
def process_single_entry(idx_program):
    idx, program = idx_program
    test_program = program.get("test_program", "")
    assertion = program.get("assertion", "")

    if test_program and assertion:
        test_code = generate_code_with_assertions(test_program, assertion)
        # Extract the Python code from the response
        exec_test_code = extract_python_code(test_code)
        # Store the extracted code in the program
        program["exec_test_code"] = exec_test_code

    return idx, program


# Function to process JSON and add the generated code with assertions
def process_json_add_assertions(input_json, output_json, num_entries=None, max_workers=5):
    with open(input_json, 'r', encoding='utf-8') as f:
        programs = json.load(f)

    # Select entries to process
    if num_entries is not None:
        selected_programs = [(idx, programs[idx]) for idx in range(min(num_entries, len(programs)))]
    else:
        selected_programs = [(idx, programs[idx]) for idx in range(len(programs))]


    # Use concurrent threads to speed up processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = list(tqdm(executor.map(process_single_entry, selected_programs), total=len(selected_programs),
                            desc="Generating assertions"))

    # Update the original programs with generated code
    for idx, updated_program in futures:
        programs[idx] = updated_program

    # Save the updated data back to the output JSON file
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(programs, f, ensure_ascii=False, indent=2)

def run_code_in_process(code: str, return_dict):
    failed = 0
    total = 0
    function_lines = []
    assert_lines = []

    for line in code.strip().split('\n'):
        if line.strip().startswith('assert '):
            assert_lines.append(line)
        else:
            function_lines.append(line)

    namespace = {}

    try:
        exec('\n'.join(function_lines), namespace)
    except Exception:
        return_dict["total"] = len(assert_lines)
        return_dict["failed"] = len(assert_lines)
        return

    for line in assert_lines:
        total += 1
        try:
            exec(line, namespace)
        except (AssertionError,RecursionError,IndexError,RuntimeError,ValueError,TypeError,ZeroDivisionError):
            failed += 1
        except Exception:
            pass

    return_dict["total"] = total
    return_dict["failed"] = failed


def safe_assert_check(code: str, timeout=20):
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    p = multiprocessing.Process(target=run_code_in_process, args=(code, return_dict))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        return -1, -1  
    return return_dict.get("total", 0), return_dict.get("failed", 0)


def run_sample_with_timeout(program, timeout=10):
    try:
        exec_test_code = program.get("exec_test_code", "")
        if exec_test_code:
            total, failed = safe_assert_check(exec_test_code, timeout)
            program["assert_total"] = total
            program["assert_failed"] = failed

            if total > 0 and failed == 0:
                program["predict_label"] = 0
            elif failed > 0:
                program["predict_label"] = 1
            else:
                program["predict_label"] = None

            # print("total:", total, "failed:", failed, "-> predict:", program["predict_label"])
        return program
    except Exception as e:
        program["error"] = str(e)
        return program


def process_assert_stat(input_json, output_json, timeout=20):
    with open(input_json, 'r', encoding='utf-8') as f:
        input_programs = json.load(f)

    if os.path.exists(output_json):
        with open(output_json, 'r', encoding='utf-8') as f:
            processed_programs = json.load(f)
        if len(processed_programs) < len(input_programs):
            processed_programs += input_programs[len(processed_programs):]
    else:
        processed_programs = input_programs.copy()

    total = len(processed_programs)
    for idx in tqdm(range(total), desc="Sequentially checking assertions"):
        program = processed_programs[idx]
        processed_programs[idx] = run_sample_with_timeout(program, timeout)
        with open(output_json, 'w', encoding='utf-8') as f_out:
            json.dump(processed_programs, f_out, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    input_json = "./process/program.json"
    output_json = "./process/program.json"

    print("🧠 Starting testing...")
    process_json_add_assertions(input_json, output_json, num_entries=None, max_workers=5)
    process_assert_stat(input_json, output_json, timeout=20)

    print("✅ All steps completed.")
