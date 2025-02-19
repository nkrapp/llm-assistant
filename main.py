import json
import requests
from assistants.functionManager import FunctionManager
from assistants.calenderManager.googleCalendar import GoogleCalendar
from assistants.calenderManager.nextcloudCalendar import NextcloudCalendar


class LLMAssistant():

    def __init__(self, port: str = "8440"):

        self.model_URL = f"http://localhost:{port}/api/prompt"

        self.google_calendar: GoogleCalendar = GoogleCalendar()
        self.nextcloud_calendar: NextcloudCalendar = NextcloudCalendar()
        self.manager: FunctionManager = FunctionManager()

        first_message = {
            "role": "system",
            "content": self.google_calendar.definePrompt()
        }
        self.messages = [first_message]
        self.tools = self.google_calendar.defineTools()
        self.tools.append(self.define_function_endConversation())

    def get_LLM_response(self, messages, tools) -> str:

        response = requests.post(
            url = self.model_URL, 
            json = {"messages": messages, "tools": tools}, 
            headers = {"accept": "application/json", "Content-Type": "application/json"}
        )
        decoded_output = response.json()["response"]["content"]
        
        # if "<|end_of_text|>" in decoded_output:
        #     decoded_output = decoded_output[0:len(decoded_output) - 15]
        return decoded_output

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

    def manager_conversation_loop(self):

        active_manager = self.manager
        while active_manager.is_alive:
            
            user_input = input("[USER]: ")
            active_manager.push_user_message(user_input)
            active_manager.unstatisfy()

            while not active_manager.is_statisfied:
                raw_response = self.get_LLM_response(active_manager.messages, active_manager.tools)
                active_manager.push_assistant_message(raw_response)

                try:
                    response = json.loads(raw_response)
                    response = response[0]
                    called_function = response["name"]
                    function_response = active_manager.handle_function_call(called_function, response["arguments"])
                    active_manager.push_user_message(function_response)

                except Exception as error:
                    active_manager.statisfy()

            print(f"[{active_manager.messages[len(active_manager.messages)-1]["role"].swapcase()}]: {active_manager.messages[len(active_manager.messages)-1]["content"]}")



    def conversation_loop(self):

        loop_condition = True

        while loop_condition:
            print(f"[{self.messages[len(self.messages)-1]["role"].swapcase()}]: {self.messages[len(self.messages)-1]["content"]}")

            user_input = input("[USER]: ")
            if user_input == "q":
                loop_condition = False
            else:
                self.messages.append({
                    "role": "user",
                    "content": user_input,
                })

                # condition for whether the assistant is ready for more input
                isWaiting = False

                while not isWaiting:
                    
                    raw_response = self.get_LLM_response(self.messages, self.tools)
                    self.messages.append({
                        "role": "assistant",
                        "content": raw_response
                    })

                    try:
                        response = json.loads(raw_response)
                        response = response[0]
                        called_function = response["name"]
                        
                        if called_function == "endConversation":
                            print("Dialogue has been terminated")
                            loop_condition = False
                            isWaiting = True
                        else: 
                            function_response = self.google_calendar.handleFunctionCall(called_function, response["arguments"])
                            self.messages.append({
                                "role": "user",
                                "content": function_response,
                            })
                    except:
                        isWaiting = True
                

               
if __name__ == "__main__":

    my_assistant = LLMAssistant()
    my_assistant.manager_conversation_loop()