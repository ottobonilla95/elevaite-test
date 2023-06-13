from _global import llm
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from langchain.schema import AgentAction, AgentFinish, LLMResult
from typing import Union, Optional
from get_tokens_count import get_tokens_count
from typing import Dict, List, Any

from _global import tokenCount
import _global
from _global import updateStatus
import re

## This is callback proc added to get some logging. Pure cut and paste from the  langchain documentation.
## 

class MyCustomCallbackHandler(BaseCallbackHandler):
    """Custom CallbackHandler."""
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Print out the prompts."""
        verbose=True
        print("")
        regex = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        toolName=re.sub(regex, "", _global.currentStatus)
        # updateStatus(toolName)
        print("@on_llm_start")
        if(prompts):
            print(prompts)
            llm.max_tokens=(3800 - get_tokens_count(str(prompts)))
            print("Maxtokens setting = " + str(get_tokens_count(str(prompts))))
        pass

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Do nothing."""
        print("@on_llm_end")
        #updateStatus("LLM_END")
        print(response)
        _global.tokenCount= _global.tokenCount + response.llm_output['token_usage']['total_tokens']
        print(_global.tokenCount)
        pass

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Do nothing."""
        #print("@on_llm_new_token")
        #print(token)
        pass

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any) -> None:
        """Do nothing."""
        print("@on_llm_error")
        print(error)
        pass

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Print out that we are entering a chain."""
        class_name = serialized["name"]
        print(f"\n\n\033[1m> Entering new {class_name} chain...\033[0m")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Print out that we finished a chain."""
        print("\n\033[1m> Finished chain.\033[0m")

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Do nothing."""
        pass

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Do nothing."""
        print("@on_tool_start")
        print(input_str)
        pass

    def on_agent_action(
        self, action: AgentAction, color: Optional[str] = None, **kwargs: Any
    ) -> Any:
        """Run on agent action."""
        color="blue"
        print("@on_agent_action")
        print(action)

    def on_tool_end(
        self,
        output: str,
        color: Optional[str] = None,
        observation_prefix: Optional[str] = None,
        llm_prefix: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """If not the final action, print out observation."""
        print("@on_tool_end")
        print(output)

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Do nothing."""
        pass

    def on_text(
        self,
        text: str,
        color: Optional[str] = None,
        end: str = "",
        **kwargs: Optional[str],
    ) -> None:
        """Run when agent ends."""
        print("@on_text")
        print(text)

    def on_agent_finish(
        self, finish: AgentFinish, color: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Run on agent end."""
        print(finish.log)
