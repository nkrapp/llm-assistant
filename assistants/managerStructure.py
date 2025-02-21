

class ManagerStructure():

    def __init__(self):
        
        self.prompt: str = ""
        self.tools: list = [self.define_function_end_conversation()]
        self.messages: list[dict[str,str]] = []

        # whether the assistant is ready to return an anwser to the user or not
        self.is_statisfied: bool = False

        # whether the assistant wants to assign the task to someone else and to whom        
        self.assigned_task_to: str = "None"

        self.is_alive: bool = True


    def handle_function_call(self, called_function: str, arguments: dict) -> str:
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

    def define_function_end_conversation(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "end_conversation",
                "description": "Call this function to end the conversation, but ONLY when the user is done with his requests and the user does not have any left questions. Before calling this function ask the user at least once if they have any left questions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                }
            }
        }
        return function