from assistants.managerStructure import ManagerStructure

class FunctionManager(ManagerStructure):

    def __init__(self):
        
        super().__init__()
        self.prompt: str = self.define_prompt()
        self.tools: list = self.append_tools()
        self.messages: list[dict[str,str]] = [{
            "role": "system",
            "content": self.prompt
        }]

    def handle_function_call(self, called_function, arguments) -> str:
        if(called_function == "endConversation"):
            self.kill()
            return "Conversation has been ended. Say goodbye to the user!"
        else:
            return "This function does not exist!"


    def append_tools(self):
        all_tools = self.tools
        tools = [

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
