import ast
import networkx as nx
import torch
import difflib
import tokenize
from io import BytesIO
import ast
import difflib
import subprocess
import json
import openai


def get_code_from_graph(graph):
    # Ensure that graph is an instance of networkx.Graph
    if not isinstance(graph, nx.Graph):
        raise ValueError("The provided object is not a valid NetworkX Graph")

    # Hypothetically, if nodes represent lines of code or tokens,
    # and they have an attribute 'code' that stores the string representation.
    code_list = []
    for node in graph.nodes(data=True):
        if 'code' in node[1]:  # node[1] gives the attribute dictionary
            code_list.append(node[1]['code'])
            
    # Joining the code list to form the complete code
    # This step is simplistic and may not represent the actual logic you need to apply
    # to correctly order and format the code lines/tokens.
    code = ' '.join(code_list)
    
    return code


def calculate_similarity(c1, c2):
    tokens1 = get_tokens(c1)
    tokens2 = get_tokens(c2)

    matcher = difflib.SequenceMatcher(None, tokens1, tokens2)
    return matcher.ratio()

def get_tokens(code):
    tokens = []
    for token in tokenize.tokenize(BytesIO(code.encode('utf-8')).readline):
        tokens.append(token.string)
    return tokens


# Extract graphs from PyG Data objects
def extract_graph_from_pyg_data(pyg_data):
    edge_index = pyg_data.edge_index
    num_nodes = pyg_data.x.size(0)

    # Create a NetworkX graph
    graph = nx.Graph()
    graph.add_nodes_from(range(num_nodes))
    graph.add_edges_from(edge_index.t().tolist())

    return graph


def estimate_updated_code(original_code, original_graph, updated_graph):
    # 1. Handle Deleted Nodes:
    deleted_nodes = [node for node in original_graph.nodes if node not in updated_graph.nodes]
    
    # 2. Handle New Nodes:
    new_nodes = [node for node in updated_graph.nodes if node not in original_graph.nodes]
    
    # Generate code snippets for new nodes
    new_code_snippets = []
    for node in new_nodes:
        # If possible, derive more logic for new nodes here:
        new_code_snippet = f"def {node}():\n    pass\n"
        new_code_snippets.append(new_code_snippet)
    
    # 3. Flexible Placeholder System:
    # This can be expanded further for different placeholders
    updated_code_lines = original_code.splitlines()
    for idx, line in enumerate(updated_code_lines):
        if line.strip() == "# Placeholder for new nodes":
            updated_code_lines[idx:idx+1] = new_code_snippets
    
    # 4. Remove or Comment out Deleted Nodes:
    for node in deleted_nodes:
        for idx, line in enumerate(updated_code_lines):
            if line.strip().startswith(f"def {node}():"):
                updated_code_lines[idx] = f"# {line}"  # Commenting out the deleted node's function
                while not updated_code_lines[idx+1].strip():  # Comment out any blank lines or further content related to the function
                    idx += 1
                    updated_code_lines[idx] = f"# {updated_code_lines[idx]}"
                break
    
    # 5. Enhanced Formatting:
    # Assuming a consistent 4-space indentation for now, but this can be adjusted
    updated_code = '\n'.join(updated_code_lines).replace("\n    ", "\n        ")  # Adjusting indentation for the new added functions

    return updated_code

def load_original_code(file_path):
    with open(file_path, 'r') as file:
        return file.read()

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
    
def get_completion(prompt, model="gpt-3.5-turbo"):

    messages = [{"role": "user", "content": prompt}]

    response = openai.ChatCompletion.create(

    model=model,

    messages=messages,

    temperature=0,

    )

    return response.choices[0].message["content"]
    
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
    
def read_code(filename):
    try:
        with open(filename, "r") as f:
            code = f.read()
        return ast.parse(code)
    except SyntaxError as e:
        print(f"Syntax error in file {filename}: {e}")
        return None

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



# Function to run Bandit and analyze the code
def run_bandit(filename):
    command = f"bandit -f json {filename}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

def analyze_bandit_results(result_json):
    # Initialize the collections for different pieces of information.
    unique_cwes = set()
    line_numbers = []
    confidences = []

    # Check if results are present in the Bandit report.
    if "results" in result_json and result_json["results"]:
        for issue in result_json["results"]:
            cwe_id = str(issue.get("issue_cwe", {}).get("id", "N/A"))  # Default to "N/A" if no CWE found
            unique_cwes.add(cwe_id)

            # Collecting details from each issue
            line_numbers.append(issue['line_number'])
            confidences.append(issue['issue_confidence'])

    # Constructing 'context' with all collected details
    context = {
        'cwe': list(unique_cwes),
        'line_numbers': line_numbers,
        'confidences': confidences
    }

    # Return both the list of unique CWEs and the context.
    return {
        'unique_cwes': list(unique_cwes),
        'context': context
    }


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
        
def generate_prompt_with_tempalte(template_id, original_code, context=None):
    """
    Generate a prompt for code fixing based on the template ID and context provided.

    Args:
    template_id (int): The template ID to use for the prompt generation.
    original_code (str): The original code snippet that needs fixing.
    context (dict, optional): The context information extracted from the code analysis. Default is None.

    Returns:
    str: The generated prompt.
    """

    # Common part of the prompt for all templates
    prompt_intro = f"I have the following Python code snippet enclosed within double quotes: \"\"\"{original_code}\"\"\""

    # Customize the prompt based on the template ID
    if template_id == 1:
        prompt = (
            f"{prompt_intro}. "
            "Please rewrite this code snippet without altering its intended functionality. "
            "Your response should only include the revised Pyhton code without explanations."
        )
    elif context is not None:  # Make sure context is provided for the other templates
        if template_id == 2:
            prompt = (
                f"{prompt_intro} There are issues at the following line numbers: {context.get('line_numbers', 'N/A')}. "
                "Rewrite the code to address these issues. Your response should only include the revised Pyhton code without explanations."
            )
        elif template_id == 3:
            prompt = (
                f"{prompt_intro} The code has weaknesses corresponding to the following CWE IDs: {context.get('cwe', 'N/A')}. "
                "Rewrite the code to address these issues. Your response should only include the revised Pyhton code without explanations."
            )
        elif template_id == 4:
            prompt = (
                f"{prompt_intro} There are issues corresponding to the CWE IDs {context.get('cwe', 'N/A')} "
                f"at the line numbers {context.get('line_numbers', 'N/A')}. Rewrite the code to address these issues. Your response should only include the revised Pyhton code without explanations."
            )
        elif template_id == 5:
            prompt = (
                f"{prompt_intro} At line numbers {context.get('line_numbers', 'N/A')}, there are issues with confidence levels: "
                f"{context.get('confidences', 'N/A')}. Rewrite the code to address these issues. Your response should only include the revised Pyhton code without explanations."
            )
        elif template_id == 6:
            prompt = (
                f"{prompt_intro} There are security weaknesses corresponding to CWE IDs {context.get('cwe', 'N/A')} with confidence levels "
                f"{context.get('confidences', 'N/A')}. Rewrite the code to address these issues. Your response should only include the revised Pyhton code without explanations."
            )
        elif template_id == 7:
            prompt = (
                f"{prompt_intro} There are security weaknesses at line numbers {context.get('line_numbers', 'N/A')} corresponding to CWE IDs "
                f"{context.get('cwe', 'N/A')} with confidence levels {context.get('confidences', 'N/A')}. Rewrite the code to address these issues. Your response should only include the revised Pyhton code without explanations."
            )
        else:
            raise ValueError(f"Unsupported template_id: {template_id}")
    else:
        raise ValueError(f"Context is required for template_id {template_id}.")

    return prompt
        


