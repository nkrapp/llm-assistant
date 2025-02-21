import json
import requests
from assistants.functionManager import FunctionManager
from assistants.calenderManager.googleCalendar import GoogleCalendar
from assistants.calenderManager.nextcloudCalendar import NextcloudCalendar

# receiving from Dialogue
# {
#   statement: string,
#   endConversation: Boolean,
# }
# sending back to dialogue
# {
#   message: string,
#   endConversation: Boolean,
# }

class LLMAssistant():

    def __init__(self, port: str = "8440"):

        self.model_URL = f"http://localhost:{port}/api/prompt"

        self.google_calendar: GoogleCalendar = GoogleCalendar()
        self.nextcloud_calendar: NextcloudCalendar = NextcloudCalendar()
        self.manager: FunctionManager = FunctionManager()

        self.history: list[dict[str,str]] = []

    def get_LLM_response(self, messages, tools) -> str:

        response = requests.post(
            url = self.model_URL, 
            json = {"messages": messages, "tools": tools}, 
            headers = {"accept": "application/json", "Content-Type": "application/json"}
        )
        decoded_output = response.json()["response"]["content"]
        
        return decoded_output


    def manager_conversation_loop(self):

        active_manager = self.manager
        while active_manager.is_alive:
            
            user_input = input("[USER]: ")
            active_manager.push_user_message(user_input)
            active_manager.unstatisfy()

            while not active_manager.is_statisfied:

                # print("getting a response from llm with following messages:")
                # for message in active_manager.messages:
                #     print(f"    [{message["role"].swapcase()}]: {message["content"]}")
                raw_response = self.get_LLM_response(active_manager.messages, active_manager.tools)
                active_manager.push_assistant_message(raw_response)
                self.history.append(active_manager.messages[-1])

                try:
                    response = json.loads(raw_response)
                    response = response[0]
                    called_function = response["name"]
                    function_response = active_manager.handle_function_call(called_function, response["arguments"])

                    assigned_task_to = active_manager.assigned_task_to
                    active_manager.assigned_task_to = "None"
                    if assigned_task_to != "None":
                        if assigned_task_to == "Manager":
                            active_manager = self.manager
                        elif assigned_task_to == "Google":
                            active_manager = self.google_calendar
                        elif assigned_task_to == "Nextcloud":
                            active_manager = self.nextcloud_calendar

                        print(f"    Switching assistant to {assigned_task_to}")
                        active_manager.push_user_message(user_input)
                        active_manager.unstatisfy()
                    else:
                        active_manager.push_user_message(function_response)

                except Exception as error:
                    active_manager.statisfy()

            print(f"[{active_manager.messages[-1]["role"].swapcase()}]: {active_manager.messages[-1]["content"]}")



               
if __name__ == "__main__":

    my_assistant = LLMAssistant()
    my_assistant.manager_conversation_loop()