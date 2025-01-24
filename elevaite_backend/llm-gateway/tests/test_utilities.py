# Utility function to generate random strings
import random
import re
import string
import pytest

from llm_gateway.utilities.onprem import get_model_endpoint
from llm_gateway.utilities.tokens import count_tokens


def generate_random_string(min_words: int, max_words: int) -> str:
    num_words = random.randint(min_words, max_words)
    words = [
        "".join(
            random.choices(
                string.ascii_letters + string.digits, k=random.randint(1, 10)
            )
        )
        for _ in range(num_words)
    ]
    return " ".join(words)


@pytest.mark.parametrize("num_strings", [1, 2, 5, 10])
def test_calculate_tokens(num_strings):
    prompts = [generate_random_string(1, 20) for _ in range(num_strings)]
    expected_tokens = sum(len(re.findall(r"\S+", string)) for string in prompts)

    assert count_tokens(prompts) == expected_tokens, (
        f"Failed for prompts: {prompts}. "
        f"Expected {expected_tokens} tokens, but got {count_tokens(prompts)}."
    )


def test_check_endpoint_success_real_call():
    model = "Llama-3.1-8B-Instruct"
    assert get_model_endpoint(model)
