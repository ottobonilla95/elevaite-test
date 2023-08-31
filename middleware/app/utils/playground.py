
import app.configs.collections_config as collections_config
import app.configs.prompts_config as prompts_config

def retrieve_prompt(llm: str, db: str, tenant: str):
    tenant = tenant.lower()
    if tenant == "cisco":
         tenant = "cisco_poc_1"
    if tenant == "netgear":
         tenant = "netgear_one_shot"
    if tenant == "pan":
         tenant = "pan_one_shot"
    if tenant == "netskope":
         tenant = "netskope_one_shot"
    # print(prompts_config.prompts_config[tenant])
    return prompts_config.prompts_config[tenant]