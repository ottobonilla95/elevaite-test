import tiktoken

## Count the tokens for given string
def get_tokens_count(query: str):
  encoding = tiktoken.encoding_for_model("text-davinci-003")
  tokenSize=encoding.encode(query)
  return(len(tokenSize))
