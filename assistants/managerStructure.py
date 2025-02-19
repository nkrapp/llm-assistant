

class ManagerStructure():

    def __init__(self):
        
        self.prompt: str = ""
        self.tools: list = [self.define_function_endConversation()]
        self.messages: list[dict[str,str]] = []

        # whether the assistant is ready to return an anwser to the user or not
        self.is_statisfied: bool = False
        
        self.is_alive: bool = True


    def handle_function_call(self, called_function: str, arguments):
        pass

    def statisfy(self):
        self.is_statisfied = True

    def unstatisfy(self):
        self.is_statisfied = False

    def kill(self):
        self.is_alive = False

    def push_user_message(self, message: str):
        self.messages.append({
            "role": "user",
            "content": message
        })
    
    def push_assistant_message(self, message: str):
        self.messages.append({
            "role": "assistant",
            "content": message
        })

    def define_function_endConversation(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "endConversation",
                "description": "Call this function to end the conversation, but ONLY the user is statisfied and the user does not have any left questions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                }
            }
        }
        return function