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

model_URL = "http://localhost:8440/api/prompt"

calendar: CalendarHelper = GoogleCalendar()
# calendar: CalendarHelper = NextcloudCalendar()

first_message = {
    "role": "system",
    "content": calendar.definePrompt()
}
messages = [first_message]
tools = calendar.defineTools()

def get_response(messages) -> str:

    response = requests.post(
        url = model_URL, 
        json = {"messages": messages, "tools": tools}, 
        headers = {"accept": "application/json", "Content-Type": "application/json"}
    )
    decoded_output = response.json()["response"]["content"]
    
    if "<|end_of_text|>" in decoded_output:
        decoded_output = decoded_output[0:len(decoded_output) - 15]
    return decoded_output


loop_condition = True

while loop_condition:
    user_input = input("[USER]: ")
    if user_input == "q":
        loop_condition = False
    else:
        messages.append({
            "role": "user",
            "content": user_input,
        })

        # condition for wether the assistant is ready for more imput
        isWaiting = False

        while not isWaiting:
            
            raw_response = get_response(messages)
            # print("response is " + raw_response)
            messages.append({
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
                    function_response = calendar.handleFunctionCall(called_function, response["arguments"])
                    messages.append({
                        "role": "user",
                        "content": function_response,
                    })
            except:
                isWaiting = True
            
            print(f"[{messages[len(messages)-1]["role"].swapcase()}]: {messages[len(messages)-1]["content"]}")

               