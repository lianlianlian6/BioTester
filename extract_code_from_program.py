import os
import ast
import json
import csv
import builtins
import argparse

# 收集 Python 内置函数名列表
builtin_functions = set(dir(builtins))

class FunctionCallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.calls = set()

    def visit_Call(self, node):
        # 支持嵌套属性调用 a.b.c -> "a.b.c"
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            parts = []
            cur = node.func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            full_name = ".".join(reversed(parts))
            self.calls.add(full_name)
        self.generic_visit(node)


def extract_functions_and_triples(file_path):
    """
    提取指定 Python 文件中的所有函数源码与调用三元组。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], []

    functions = []
    triples = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            try:
                func_code = ast.get_source_segment(source, node)
                func_name = node.name
                functions.append((func_name, func_code))

                visitor = FunctionCallVisitor()
                visitor.visit(node)

                for callee in visitor.calls:
                    if not callee or not isinstance(callee, str):
                        continue
                    relation = "uses" if callee in builtin_functions else "calls"
                    triples.append((func_name, relation, callee))
            except Exception as e:
                print(f"跳过函数 {node.name}，原因：{e}")
                continue

    return functions, triples


def process_directory(input_dir):
    """
    主处理函数：遍历目录，生成函数定义 JSON 与函数调用三元组 CSV。
    """
    json_output = './process/program.json'
    csv_output = './process/knowledge_database.csv'

    all_functions = []
    all_triples = []
    func_id = 0

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    functions, triples = extract_functions_and_triples(file_path)
                    for name, code in functions:
                        all_functions.append({'id': func_id, 'test_program': code})
                        func_id += 1
                    all_triples.extend(triples)
                except Exception as e:
                    print(f"Error in {file_path}：{e}")

    # 创建输出目录
    os.makedirs('./process', exist_ok=True)

    # 写入 JSON
    with open(json_output, 'w', encoding='utf-8') as jf:
        json.dump(all_functions, jf, indent=2, ensure_ascii=False)

    # 写入 CSV
    with open(csv_output, 'w', newline='', encoding='utf-8') as cf:
        writer = csv.writer(cf)
        writer.writerow(['caller', 'relation', 'callee'])
        writer.writerows(all_triples)

def main():
    parser = argparse.ArgumentParser(description="Extracting test code")
    parser.add_argument('--input_dir', type=str, required=True, help='Python program root directory')
    args = parser.parse_args()

    process_directory(args.input_dir)

if __name__ == '__main__':
    main()