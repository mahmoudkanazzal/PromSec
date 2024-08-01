import ast
import networkx as nx
import torch
import difflib
import tokenize
from io import BytesIO
import subprocess
import json


def generate_graph_from_ast(node):
    """
    Generate a graph from an Abstract Syntax Tree (AST).

    Parameters:
        node (ast.AST): The root node of the AST.

    Returns:
        nx.Graph: Graph representation of the AST.
    """
    G = nx.Graph()

    def traverse_tree(curr_node, parent_id=None):
        nonlocal node_id
        curr_id = node_id
        G.add_node(curr_id, features=get_node_features(curr_node))

        if parent_id is not None:
            G.add_edge(parent_id, curr_id)

        parent_id = curr_id
        node_id += 1

        for child in ast.iter_child_nodes(curr_node):
            traverse_tree(child, parent_id)

    node_id = 0
    traverse_tree(node)
    return G


def get_node_features(node):
    """
    Extract binary features from AST nodes.

    Parameters:
        node (ast.AST): The node from which to extract features.

    Returns:
        list: List of binary features extracted from the node.
    """
    features = []

    has_function_def = any(isinstance(child, ast.FunctionDef) for child in ast.iter_child_nodes(node))
    features.append(int(has_function_def))

    has_loop = any(isinstance(child, (ast.For, ast.While)) for child in ast.iter_child_nodes(node))
    features.append(int(has_loop))

    has_conditional = any(isinstance(child, ast.If) for child in ast.iter_child_nodes(node))
    features.append(int(has_conditional))

    has_comment = any(isinstance(child, ast.Expr) and isinstance(child.value, ast.Str) for child in ast.iter_child_nodes(node))
    features.append(int(has_comment))

    # Add more binary features as needed...

    return features


def adjacency_matrix_to_edge_index(adj_matrix):
    """
    Convert an adjacency matrix to edge indices.

    Parameters:
        adj_matrix (scipy.sparse.csr_matrix): Adjacency matrix.

    Returns:
        torch.Tensor: Edge indices in the form of a tensor.
    """
    edge_index = torch.tensor(adj_matrix.nonzero(), dtype=torch.long)
    return edge_index


def calculate_vcs2(code_graph):
    # Assume that code_graph is a valid graph representation of the code
    
    # Convert the graph to a code file (e.g., a .py file)
    code_filename = "temp_code.py"
    with open(code_filename, "w") as code_file:
        code_file.write(code_graph)
    
    # Run Bandit analysis on the code file
    command = f"bandit -f json {code_filename}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    analysis_result = result.stdout
    
    # Parse the Bandit analysis result
    result_json = json.loads(analysis_result)
    
    cwe_set = set()  # Use a set to store identified unique CWEs
    
    if "results" in result_json:
        for issue in result_json["results"]:
            if "issue_cwe" in issue and "id" in issue["issue_cwe"]:
                cwe_set.add(issue["issue_cwe"]["id"])  # Add the CWE to the set (duplicates are automatically handled)
    
    cwe_count = len(cwe_set)  # Count of unique CWEs
    cwe_list = list(cwe_set)  # Convert the set to a list for the return value
    
    return cwe_count, cwe_list  # Return both the count and the list of unique CWEs


def calculate_similarity1(c1, c2):
    tokens1 = get_tokens(c1)
    tokens2 = get_tokens(c2)

    matcher = difflib.SequenceMatcher(None, tokens1, tokens2)
    return matcher.ratio()


def get_tokens(code):
    tokens = []
    for token in tokenize.tokenize(BytesIO(code.encode('utf-8')).readline):
        tokens.append(token.string)
    return tokens


class NormalizeNames(ast.NodeTransformer):
    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id='_VAR_', ctx=node.ctx), node)
    
    def visit_FunctionDef(self, node):
        node.name = "_FUNC_"
        return self.generic_visit(node)


def get_normalized_ast(code):
    tree = ast.parse(code)
    normalizer = NormalizeNames()
    normalized_tree = normalizer.visit(tree)
    return normalized_tree


def ast_structure(node):
    if isinstance(node, ast.AST):
        node_tag = type(node).__name__
        children = [ast_structure(child) for child in ast.iter_child_nodes(node)]
        if children:
            return {node_tag: children}
        else:
            return node_tag
    else:
        return str(node)


def calculate_similarity2(tree1, tree2):
    matcher = difflib.SequenceMatcher(None, str(tree1), str(tree2))
    return matcher.ratio()


def calculate_similarity(c1, c2):
    tokens1 = get_tokens(c1)
    tokens2 = get_tokens(c2)

    matcher = difflib.SequenceMatcher(None, tokens1, tokens2)
    return matcher.ratio()


def calculate_vcs(code_graph):
    # Assume that code_graph is a valid graph representation of the code
    
    # Convert the graph to a code file (e.g., a .py file)
    code_filename = "temp_code.py"
    with open(code_filename, "w") as code_file:
        code_file.write(code_graph)
    
    # Run Bandit analysis on the code file
    command = f"bandit -f json {code_filename}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    analysis_result = result.stdout
    
    # Parse the Bandit analysis result
    result_json = json.loads(analysis_result)
    
    cwe_set = set()  # Use a set to store identified unique CWEs
    
    if "results" in result_json:
        for issue in result_json["results"]:
            if "issue_cwe" in issue and "id" in issue["issue_cwe"]:
                cwe_set.add(issue["issue_cwe"]["id"])  # Add the CWE to the set (duplicates are automatically handled)
    
    cwe_count = len(cwe_set)  # Count of unique CWEs

    return cwe_count


# Extract graphs from PyG Data objects
def extract_graph_from_pyg_data(pyg_data):
    edge_index = pyg_data.edge_index
    num_nodes = pyg_data.x.size(0)

    # Create a NetworkX graph
    graph = nx.Graph()
    graph.add_nodes_from(range(num_nodes))
    graph.add_edges_from(edge_index.t().tolist())

    return graph


def load_original_code(file_path):
    with open(file_path, 'r') as file:
        return file.read()
        
        
       
        
def compare_asts(tree1, tree2):
    """
    Compare two ASTs and return a similarity measure.
    """
    nodes1 = list(ast.walk(tree1))
    nodes2 = list(ast.walk(tree2))

    common_nodes = len([node for node in nodes1 if any(isinstance(node, type(other)) for other in nodes2)])

    return common_nodes / max(len(nodes1), len(nodes2))


def calc_diff(code1, code2):
    try:
        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)
        return compare_asts(tree1, tree2)
    except SyntaxError:
        print("Syntax error encountered while calculating AST difference.")
        return float('inf')  # Return a large value to indicate a "large difference" due to the syntax error.
             
        
        
        
def compare_asts(tree1, tree2):
    """
    Compare two ASTs and return a similarity measure.
    """
    nodes1 = list(ast.walk(tree1))
    nodes2 = list(ast.walk(tree2))

    common_nodes = len([node for node in nodes1 if any(isinstance(node, type(other)) for other in nodes2)])

    return common_nodes / max(len(nodes1), len(nodes2))


def calc_diff(code1, code2):
    try:
        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)
        return compare_asts(tree1, tree2)
    except SyntaxError:
        print("Syntax error encountered while calculating AST difference.")
        return float('inf')  # Return a large value to indicate a "large difference" due to the syntax error.
    
    
# Define the VCS function
def VCS(generated_graph):
    adjacency_matrix = (generated_graph > 0).int()
    # Convert adjacency matrix to an edge list
    edges = torch.nonzero(adjacency_matrix, as_tuple=False)
    # Generate a code representation from the edge list
    code_lines = []
    for edge in edges:
        code_line = f"add_edge({edge[0]}, {edge[1]})"
        code_lines.append(code_line)
    code_representation = "\n".join(code_lines)
    # Now, pass the code representation to the calculate_vcs function
    cwe_count = calculate_vcs(code_representation)
    return cwe_count

import subprocess
import json
from prettytable import PrettyTable
import matplotlib.pyplot as plt

def run_bandit(filename):
    command = f"bandit -f json {filename}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout



import ast
import networkx as nx

def generate_cfg_from_code(file_path):
    with open(file_path, 'r') as f:
        code = f.read()

    # Parse the Python source code into an AST
    tree = ast.parse(code)

    # Start generating the CFG
    cfg = nx.DiGraph()
    build_cfg_from_ast(tree, cfg)

    return cfg

def build_cfg_from_ast(node, graph, prev_node=None):
    # Handle simple statements by just adding them as nodes in the graph
    if isinstance(node, ast.stmt):
        current_node = str(node.lineno)
        graph.add_node(current_node, ast_node=node)

        if prev_node is not None:
            graph.add_edge(prev_node, current_node)

        # Special handling for control structures
        if isinstance(node, ast.If):
            build_cfg_from_ast(node.body, graph, current_node)
            build_cfg_from_ast(node.orelse, graph, current_node)
            return
        elif isinstance(node, (ast.For, ast.While)):
            build_cfg_from_ast(node.body, graph, current_node)
            return

        prev_node = current_node

    # If it's not a simple statement, it's a list of statements (like body of If, For, etc.)
    elif isinstance(node, list):
        for child in node:
            prev_node = build_cfg_from_ast(child, graph, prev_node)

    return prev_node




def get_node_features(graph, node):
    """
    Extract binary features from CFG nodes.

    Parameters:
        graph (DiGraph): The graph containing the node.
        node: The node from which to extract features.

    Returns:
        list: List of binary features extracted from the node.
    """
    features = []

    # Get node attributes from the graph
    node_data = graph.nodes[node]

    # Extract binary features from node attributes. 
    # Assumes that these attributes exist in your CFG, you might need to adjust
    has_function_def = node_data.get('contains_function', False)
    features.append(int(has_function_def))

    has_loop = node_data.get('contains_loop', False)
    features.append(int(has_loop))

    has_conditional = node_data.get('contains_if', False)
    features.append(int(has_conditional))

    has_comment = node_data.get('contains_comment', False)  # This might be tricky for CFGs, might not be applicable
    features.append(int(has_comment))

    # Add more binary features as needed...

    return features

