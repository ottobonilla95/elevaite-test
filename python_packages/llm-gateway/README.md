## Installation

Add as your UV dependency or include in your `requirements.txt` as an editable:

```txt
-e path/to/llm-gateway
```

## Setup

To get started, you need to configure your environment variables. Copy the environment variable template file to a new or pre-existing `.env` file in your project's root directory:

```bash
cp tests/.env.example .env
```

Edit the newly created `.env` file to include llm-gateway specific configurations.

## Usage

```python
from llm_gateway.services import RequestType, UniversalService
from llm_gateway.models.text_generation.core.interfaces import (
    TextGenerationType,
)

# Using UniversalService for all implications
# but you can use a request-specific service as well
service = UniversalService()

sys_msg = "You are a wizard's assistant."
prompt = "Help me create a level 50 elixir.."

provider_type = TextGenerationType.ON_PREM
additional_props = {"role": "assistant"}

config = {"type": provider_type.value, **additional_props}

response = service.handle_request(
    request_type=RequestType.TEXT_GENERATION,
    provider_type=provider_type,
    prompt=prompt,
    sys_msg=sys_msg,
    model_name="Llama-3.1-8B-Instruct",
    retries=5,
    max_tokens=1250,
    temperature=1,
    config=config,
)

print(f"Response: {response.text}")
print(f"Tokens In: {response.tokens_in}, Tokens Out: {response.tokens_out}")
print(f"Latency: {response.latency} ms")
```

For additional examples and usage details, refer to the `/tests` directory.

## Running Tests

To run the tests, make sure you have a `.env` file at the same level as `tests/.env.example`, then execute:

```bash
pytest
```

This will run the full test suite to verify that everything is set up correctly.

## More information
Refer to `/documentation`