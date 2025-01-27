import os
import os.path
from dotenv import load_dotenv
import datetime
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from calendarHelper import CalendarHelper
import ast


# Load environment variables from .env file
load_dotenv()
date = datetime.datetime.now().isoformat()
calendar: CalendarHelper = CalendarHelper()
model_URL = "http://localhost:8440/api/prompt"
main_prompt = {
    "role": "system",
    "content": f"""
        You are a helpful dialogue-assistant with tool calling capabilities, that allow you to access and change a calendar. Todays date is {date}. 
        
        After every message decide if you want to call a function or anwser with plain text. You CANNOT do both. Keep the conversation going until the user specifically wants to end the conversation. DON'T end the conversation to early.
        Respond with the function you want to use if you decide to call a function, else respond with plain text.

        Here are the different colorIds you should use:
        '10' - green and music related, 
        '5' - yellow and Friends related, 
        '4' - light red and study related, 
        '8' - grey and used when unsure",

        If you are calling a function: Always put the object inside a list. Do not write an introduction or summary.
    """
}

error_handler_prompt = "Think about what might have been your mistake and try again now."

messages = [main_prompt]
tools = calendar.defineTools()

def get_response(messages) -> str:

    # trick to save memory
    # messages = messages[-5:]

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
error_counter = 0
error_tollerance = 2

while loop_condition:
    user_input = input("[USER]: ")
    if user_input == "q":
        loop_condition = False
    else:
        messages.append({
            "role": "user",
            "content": user_input,
        })

        # condition for weather the assistant is ready for more imput
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
                
                if called_function == "getEvents":
                    events = calendar.getEvents(
                        timeFrom = response["arguments"]["timeFrom"], 
                        timeTill = response["arguments"]["timeTill"]
                    )
                    if len(events) == 0:
                        messages.append({
                            "role": "user",
                            "content": f"There are no upcoming events."
                        })
                    else:
                        messages.append({
                            "role": "user",
                            "content": f"The events for the asked time are: {events}."
                        })
                elif called_function == "putEvent":
                    try:
                        print("Before calendar putEvent")
                        event = calendar.putEvent(
                            summary = response["arguments"]["summary"], 
                            timeFrom = response["arguments"]["timeFrom"], 
                            timeTill = response["arguments"]["timeTill"],
                            description = response["arguments"]["description"] if "description" in response["arguments"] else None,
                            colorId = response["arguments"]["colorId"] if "colorId" in response["arguments"] else None
                        )
                        messages.append({
                            "role": "user",
                            "content": f"Following event was created: {event}."
                        })
                    except Exception as error:
                        if(error_counter < error_tollerance):
                            messages.append({
                                "role": "user",
                                "content": f"The event could not be created because of {error}. {error_handler_prompt}"
                            })
                            error_counter += 1
                        else:
                            messages.append({
                                "role": "user",
                                "content": f"The event could not be created because of {error}. Excuse yourself in front of the user."
                            })
                            error_counter = 0
                elif called_function == "deleteEvent":
                    try:
                        calendar.deleteEvent(eventId = response["arguments"]["eventId"])
                        messages.append({
                            "role": "user",
                            "content": f"The event was deleted successfully"
                        })
                    except Exception as error:
                        if(error_counter < error_tollerance):
                            messages.append({
                                "role": "user",
                                "content": f"The event could not be deleted because of {error}. {error_handler_prompt}"
                            })
                            error_counter += 1
                        else:
                            messages.append({
                                "role": "user",
                                "content": f"The event could not be deleted because of {error}. Excuse yourself in front of the user."
                            })
                            error_counter = 0
                elif called_function == "editEvent":
                    try:
                        event = calendar.editEvent(
                            eventId = response["arguments"]["eventId"],
                            timeFrom = response["arguments"]["timeFrom"] if "timeFrom" in response["arguments"] else None,
                            timeTill = response["arguments"]["timeTill"] if "timeTill" in response["arguments"] else None,
                            summary = response["arguments"]["summary"] if "summary" in response["arguments"] else None,
                            description = response["arguments"]["description"] if "description" in response["arguments"] else None,
                            colorId = response["arguments"]["colorId"] if "colorId" in response["arguments"] else None
                        )
                        messages.append({
                            "role": "user",
                            "content": f"Following event was edited: {event}."
                        })
                    except Exception as error:
                        if(error_counter < error_tollerance):
                            messages.append({
                                "role": "user",
                                "content": f"The event could not be edited because of {error}. {error_handler_prompt}"
                            })
                            error_counter += 1
                        else:
                            messages.append({
                                "role": "user",
                                "content": f"The event could not be edited because of {error}. Excuse yourself in front of the user."
                            })
                            error_counter = 0
                elif called_function == "endConversation":
                    print("Dialogue has been terminated")
                    loop_condition = False
                    isWaiting = True
            except:
                isWaiting = True
            
            print(f"[{messages[len(messages)-1]["role"].swapcase()}]: {messages[len(messages)-1]["content"]}")

               