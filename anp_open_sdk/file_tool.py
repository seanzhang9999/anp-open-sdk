import json

from cryptography.hazmat.primitives import serialization


def load_private_key_from_path(private_key_path):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )
    return private_key


def load_did_doc_from_path(did_document_path):
    with open(did_document_path, 'r') as f:
        did_document = json.load(f)
    return did_document
