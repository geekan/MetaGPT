from typing import Union

from transformers import AutoTokenizer


def jaccard_retriever(traceback: str, candidates: list):
    """
    Retrieve symbol changes based on the jaccard similarity

    Args:
        traceback: the traceback of the error
        candidates: the symbol changes list

    Returns:
        ranges: the index of the symbol changes list after sorting based on the jaccard similarity
    """
    tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-350M-multi", cache_dir="cache")
    # candidates is a list of code strings
    sim_scores = []
    for i, candidate in enumerate(candidates):
        sim_scores.append((i, jaccard_similarity(traceback, candidate, tokenizer)))

    # sort the candidate index based on the edit similarity in a descending order
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    # only return the index
    ranks = [index for index, score in sim_scores]

    return ranks


def jaccard_similarity(
    traceback: Union[str, list], candidate: Union[str, list], tokenizer: AutoTokenizer = None
) -> float:
    # Check input types and tokenize/de-duplicate as needed
    if isinstance(traceback, str):
        assert tokenizer, "tokenizer must be provided if input is string"
        traceback = set(tokenizer.tokenize(traceback))
    elif isinstance(traceback, list):
        traceback = set(traceback)

    if isinstance(candidate, str):
        assert tokenizer, "tokenizer must be provided if input is string"
        candidate = set(tokenizer.tokenize(candidate))
    elif isinstance(candidate, list):
        candidate = set(candidate)

    try:
        return len(traceback.intersection(candidate)) / len(traceback.union(candidate))
    except ZeroDivisionError:
        print("ZeroDivisionError")
        print(traceback, candidate)
        return 0
