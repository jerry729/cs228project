import numpy
from tree_sitter import Language, Parser
import os
import sys
import torch
from transformers import RobertaTokenizer, RobertaConfig, RobertaModel
from transformers import AutoTokenizer, AutoModel

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = RobertaTokenizer.from_pretrained("microsoft/codebert-base")
model = RobertaModel.from_pretrained("microsoft/codebert-base")
model.to(device)


C_SHARP_LANGUAGE = Language('parser/my-languages.so', 'c_sharp')
JAVA_LANGUAGE = Language('parser/my-languages.so', 'java')

# Stolen from some Github issue, need to find the link for reference
def traverse_tree(tree):
    cursor = tree.walk()

    reached_root = False
    while reached_root == False:
        yield cursor.node

        if cursor.goto_first_child():
            continue

        if cursor.goto_next_sibling():
            continue

        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True

            if cursor.goto_next_sibling():
                retracing = False


# CodetT5 unique identifiers all recieve a unique identifer 
def get_ast_vector(full_method, language="java"):
    parser = Parser()

    if language == "java":
        parser.set_language(JAVA_LANGUAGE)
        full_method = "public class App {" + full_method + "}"
    else:
        parser.set_language(C_SHARP_LANGUAGE)

    data = full_method
    byte = bytearray(data.encode())
    tree = parser.parse(byte)

    nodes = []

    identifiers = []
    identifiers_ids = {}

    for node in traverse_tree(tree):
        if node.is_named:
            if node.type == "identifier":
                identifiers.append(full_method[node.start_byte:node.end_byte])

            nodes.append(node)

    if language == "java":
        nodes = nodes[5:]

    init_id = 0

    for identifier in identifiers:
        if identifier not in identifiers_ids:
            identifiers_ids[identifier] = init_id
            init_id += 1

    vector = []

    for node in nodes:
        node_body = full_method[node.start_byte:node.end_byte]

        if node_body in identifiers:
            vector.append(identifiers_ids[node_body])
        else:
            vector.append(0)

    return vector

