import pandas as pd
from pyvis.network import Network
import os
import builtins

def visualize_knowledge_graph():
    # === 配置参数 ===
    csv_path = './process/knowledge_database.csv'
    output_dir = './process'

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(csv_path):
        print(f"[Error] CSV file not found: {csv_path}")
        return

    # === 读取数据 ===
    df = pd.read_csv(csv_path)
    sub_df = df

    net = Network(height="800px", width="100%", directed=True)
    net.force_atlas_2based()

    nodes = set()
    indegree = {}
    outdegree = {}
    edge_list = []

    builtin_funcs = set(dir(builtins))
    aims_related_nodes = set()

    # === 构建节点与边 ===
    for _, row in sub_df.iterrows():
        caller = str(row['caller']) if 'caller' in row else str(row['subject'])
        callee = str(row['callee']) if 'callee' in row else str(row['object'])
        relation = row['relation']

        indegree[callee] = indegree.get(callee, 0) + 1
        outdegree[caller] = outdegree.get(caller, 0) + 1

        edge_list.append((caller, callee, relation))
        nodes.update([caller, callee])

        if relation == 'aims':
            aims_related_nodes.add(callee)

    outgoing_relations = {}
    for caller, callee, relation in edge_list:
        outgoing_relations.setdefault(caller, set()).add(relation)

    for node in nodes:
        in_deg = indegree.get(node, 0)
        out_deg = outdegree.get(node, 0)
        out_rels = outgoing_relations.get(node, set())

        if node in aims_related_nodes:
            color = "#22c55e"  # green
        else:
            if in_deg == 0:
                color = "#a855f7"  # purple: top-level
            elif in_deg > 0:
                if node in builtin_funcs:
                    color = "#9ca3af"  # gray: builtin
                elif out_rels == {"aims"} and out_deg == 1:
                    color = "#3b82f6"  # blue bottom
                else:
                    color = "#f97316" # default orange (intermediate)
            else:
                color = "#9ca3af"  # gray: isolated

        net.add_node(node, label=node, color=color)

    for caller, callee, relation in edge_list:
        if relation == 'uses':
            edge_color = "#9ca3af"  # gray: builtin
        elif relation == 'calls':
            edge_color = "#f97316"  # orange-red
        elif relation == 'aims':
            edge_color = "#22c55e"  # green
        else:
            edge_color = "#94a3b8"  # default: slate

        net.add_edge(caller, callee, label=relation, color=edge_color)

    # === 输出 HTML 图谱 ===
    html_path = os.path.join(output_dir, f"Knowledge_Graph.html")
    net.write_html(html_path)
    print(f"[✓] Knowledge graph generated: {html_path}")

if __name__ == '__main__':
    visualize_knowledge_graph()
