import os.path
from dotenv import load_dotenv
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from calendarHelper.calendarHelper import CalendarHelper
from calendarHelper.googleCalendar import GoogleCalendar
from calendarHelper.nextcloudCalendar import NextcloudCalendar
import ast







class LLMAssistant():

    def __init__(self, port: str = "8440"):

        self.model_URL = f"http://localhost:{port}/api/prompt"

        self.calendar: CalendarHelper = GoogleCalendar()
        # self.calendar: CalendarHelper = NextcloudCalendar()

        first_message = {
            "role": "system",
            "content": self.calendar.definePrompt()
        }
        self.messages = [first_message]
        self.tools = self.calendar.defineTools()
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
                "description": "Call this function to end the conversation, but ONLY after at least two messages from the user and ONLY if it seems appropriate and the user does not have any left questions",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                }
            }
        }
        return function

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
                            function_response = self.calendar.handleFunctionCall(called_function, response["arguments"])
                            self.messages.append({
                                "role": "user",
                                "content": function_response,
                            })
                    except:
                        isWaiting = True
                

               
if __name__ == "__main__":

    my_assistant = LLMAssistant()
    my_assistant.conversation_loop()