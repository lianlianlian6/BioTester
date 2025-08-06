import json
import time
import concurrent.futures
import multiprocessing
from tqdm import tqdm

def execute_code(code, testcase):
    """在子进程中执行一段代码，返回执行结果"""
    local_env = {}
    try:
        # 先执行函数定义
        exec(code, {}, local_env)
        # 再执行testcase
        result = eval(testcase, {}, local_env)
        return ("success", repr(result))
    except Exception as e:
        return ("error", str(e))


def run_with_timeout(code, testcase, timeout=10):
    """设置子进程执行，防止死循环"""
    with multiprocessing.Pool(1) as pool:
        result = pool.apply_async(execute_code, (code, testcase))
        try:
            status, output = result.get(timeout=timeout)
            return status, output
        except multiprocessing.context.TimeoutError:
            pool.terminate()
            return "timeout", "Timeout exceeded"


def run_code_and_collect_assertions(code, testcase_block):
    """对每一条用例，执行并生成断言"""
    assertions = []

    for line in testcase_block.strip().split('\n'):
        line = line.strip()
        if not line:
            continue

        status, output = run_with_timeout(code, line, timeout=20)

        if status == "success":
            assertion = f"assert {line} == {repr(output)}"
        elif status == "error":
            assertion = f"# Failed to execute {line}: {output}"
        elif status == "timeout":
            assertion = f"# Timeout when executing {line}"

        assertions.append(assertion)

    return assertions


def process_single_program(idx_program):
    idx, program = idx_program
    code = program.get("generation", "")
    testcase_block = program.get("testcase", "")

    if code and testcase_block:
        assertions = run_code_and_collect_assertions(code, testcase_block)
        program["assertion"] = assertions
        # print(assertions)
        time.sleep(1)
    return idx, program


def process_json_generate_assertions(input_json, output_json, num_entries=None, max_workers=5):
    with open(input_json, 'r', encoding='utf-8') as f:
        programs = json.load(f)

    filtered_programs = [(idx, programs[idx]) for idx in range(len(programs))]

    if num_entries is not None:
        selected_programs = [(idx, programs[idx]) for idx in range(min(num_entries, len(filtered_programs)))]
    else:
        selected_programs = filtered_programs

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = list(tqdm(executor.map(process_single_program, selected_programs), total=len(selected_programs),
                            desc="Generating assertions"))

    for idx, updated_program in futures:
        programs[idx] = updated_program

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(programs, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')  # Windows 必须加
    input_json = "./process/program.json"
    output_json = "./process/program.json"
    print("🧠 Starting oracle generation...")
    process_json_generate_assertions(input_json, output_json, num_entries=None, max_workers=5)
    print("✅ Oracle generation completed.")