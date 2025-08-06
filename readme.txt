---

# README

This project provides a multi-stage pipeline for analyzing and enhancing the functions within a target software system. The workflow includes function extraction, intention summarization, knowledge graph construction, semantic alignment, assertion generation, and bug detection. Each step is implemented as a standalone Python script.

## 🧭 Workflow Overview

### Step 1: Function Extraction

Run the following command to extract all functions from the target software project:

```bash
python extract_code_from_program.py --input_dir <path_to_target_project>
```

* **Description**: This step parses the input software project and extracts each function as an independent unit for further analysis.

---

### Step 2: Intention Summarization

Run:

```bash
python intention_for_code.py
```

* **Description**: Uses a fine-tuned large language model to generate a concise natural language intention summary for each extracted function.
* **Note**: Please manually set the values of `BASE_MODEL` and `ADAPTER_PATH` at the beginning of this script.

---

### Step 3: Knowledge Graph Visualization

Run:

```bash
python visualize_knowledge_graph.py
```

* **Description**: Builds and visualizes a structural knowledge graph for the software project based on internal function dependencies.

---

### Step 4: Textual Retrieval

Run:

```bash
python text_retrieval_for_code.py --folder_path <path_to_reference_pdfs>
```

* **Description**: For each function, retrieves semantically relevant sentences from the provided set of reference PDF documents.
* **Note**: Please set `BASE_MODEL` and `ADAPTER_PATH` in the script header.

---

### Step 5: Detail Generation

Run:

```bash
python detail_generation.py
```

* **Description**: Uses the knowledge graph and retrieved texts to generate a detailed algorithm description for each function. Pseudocode is then automatically synthesized from this description.
* **Note**: You must manually configure `openai.api_key` in this script.

---

### Step 6: Code Generation

Run:

```bash
python code_generation.py
```

* **Description**: Translates the pseudocode into executable function code while preserving the original coding style.
* **Note**: `openai.api_key` must also be set here.

---

### Step 7: Semantic Alignment

Run:

```bash
python semantic_alignment.py
```

* **Description**: Performs semantic similarity comparison between the original and the generated code.
* **Note**: Be sure to specify the value of `MODEL_NAME` at the beginning of this script.

---

### Step 8: Assertion Generation

Run:

```bash
python assertion_generation.py
```

* **Description**: Automatically generates assertions for each function unit based on its inferred behavior.

---

### Step 9: Bug Detection

Run:

```bash
python bug_detection.py
```

* **Description**: Uses the generated assertions to test the function units and identify inputs that cause runtime errors.
* **Note**: `openai.api_key` must also be set in this script.

---

## 🗂 Output Organization

All intermediate and final outputs are saved in the `process` folder. In particular:

* `program.json` stores all function units along with their corresponding intention summaries, algorithm descriptions, assertions, and more.
* The knowledge graph and visualization results are also saved under `process`.

---

## ⚠️ Manual Configuration Required

Please set the following variables before execution:

| Script                       | Variable(s) to Set           |
| ---------------------------- | ---------------------------- |
| `intention_for_code.py`      | `BASE_MODEL`, `ADAPTER_PATH` |
| `text_retrieval_for_code.py` | `BASE_MODEL`, `ADAPTER_PATH` |
| `semantic_alignment.py`      | `MODEL_NAME`                 |
| `detail_generation.py`       | `openai.api_key`             |
| `code_generation.py`         | `openai.api_key`             |
| `bug_detection.py`           | `openai.api_key`             |

---

## 📌 Notes

* This pipeline assumes a function-level granularity for unit analysis.
* All outputs are structured and stored for easy inspection and downstream evaluation.
* The OpenAI API is used for several tasks and requires an active API key.
