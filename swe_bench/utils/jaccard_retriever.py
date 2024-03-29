from typing import Union

from transformers import AutoTokenizer


def jaccard_retriever(code, candidates: list, similarity: str = "jaccard"):
    tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-350M-multi", cache_dir="cache")
    # check if the similarity is valid
    assert similarity == "jaccard", "similarity must be one of edit, jaccard, cosine"

    # candidates is a list of code strings
    sim_scores = []
    for i, candidate in enumerate(candidates):
        sim_scores.append((i, jaccard_similarity(code, candidate, tokenizer)))

    # sort the candidate index based on the edit similarity in a descending order
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    # only return the index
    ranks = [index for index, score in sim_scores]

    return ranks


def jaccard_similarity(code1: Union[str, list], code2: Union[str, list], tokenizer: AutoTokenizer = None) -> float:
    # Check input types and tokenize/de-duplicate as needed
    if isinstance(code1, str):
        assert tokenizer, "tokenizer must be provided if input is string"
        code1 = set(tokenizer.tokenize(code1))
    elif isinstance(code1, list):
        code1 = set(code1)

    if isinstance(code2, str):
        assert tokenizer, "tokenizer must be provided if input is string"
        code2 = set(tokenizer.tokenize(code2))
    elif isinstance(code2, list):
        code2 = set(code2)

    try:
        return len(code1.intersection(code2)) / len(code1.union(code2))
    except ZeroDivisionError:
        print("ZeroDivisionError")
        print(code1, code2)
        return 0
