from assistants.managerStructure import ManagerStructure
from typing import Literal


class FunctionManager(ManagerStructure):

    def __init__(self):
        
        super().__init__()
        self.prompt: str = self.define_prompt()
        self.tools: list = self.append_tools()
        self.messages: list[dict[str,str]] = [{
            "role": "system",
            "content": self.prompt
        }]

    def handle_function_call(self, called_function: str, arguments: dict) -> str:
        if called_function == "end_conversation":
            self.kill()
            return "Conversation has been ended. Say goodbye to the user!"
        elif called_function == "assign_task_to":
            self.assigned_task_to = arguments["target"]
            return ""
        else:
            return "This function does not exist!"


    def append_tools(self):
        all_tools = self.tools
        tools = [
            self.define_function_assign_task_to(),
        ]
        for tool in tools:
            all_tools.append(tool)
        return all_tools

    def get_tools(self) -> list[str]:
        return self.tools
    
    def define_prompt(self):
        file = open("assistants/functionManagerPrompt.txt", "r")
        prompt = file.read()
        return prompt

    def define_function_assign_task_to(self):
        function = {
            "type": "function",
            "function": {
                "name": "assign_task_to",
                "description": "Assign the task to the assistant who manages the topic that matches the user request.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": ["Google", "Nextcloud"]}
                    },
                    "required": ["target"],
                }
            }
        }
        return function