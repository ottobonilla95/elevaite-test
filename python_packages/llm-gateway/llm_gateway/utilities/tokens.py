import re
from typing import List


def count_tokens(strings: List[str]) -> int:
    """
    This method isn't exactly accurate. Depending on the LLM the amount of tokens differs.
    :param strings: A list of strings making up for one prompt.
    """
    return sum(len(re.findall(r"\S+", string)) for string in strings)
