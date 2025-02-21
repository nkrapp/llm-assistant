import os
import os.path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from assistants.managerStructure import ManagerStructure
import datetime

# color_ids:
"""
blue / lavendel: -
light green / Salbei: 2
purple / Weintraube: 3
light red / Flamingo: 4
Yellow / Banane: 5
Orange / Mandarine: 6
light blue / Pfau: 7
grey / Graphit: 8
dark blue / Heidelbeere: 9 
Green / Basilikum: 10
red / Tomate: 11
"""


class GoogleCalendar(ManagerStructure):

    def __init__(self):
        super().__init__()
        # Load environment variables from .env file
        load_dotenv()
        
        # If modifying these scopes, delete the file token.json.
        SCOPES = ['https://www.googleapis.com/auth/calendar']

        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.

        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        for tool in [
            self.define_function_get_events(),
            self.define_function_put_event(),
            self.define_function_delete_event(),
            self.define_function_edit_event(),
            self.define_function_call_for_help()
        ]:
            self.tools.append(tool)
        
        self.today = datetime.datetime.now().isoformat()
        self.prompt = f"""
You are a helpful dialogue-assistant with tool calling capabilities, that allow you to access and change a calendar. Your ONLY purpose is to manage the users Google Calendar and nothing else.
Have a pleasant conversation with the user and try to help them with their tasks regarding the calendar. If the topic is not about the users calendar you have to call for help with the specific function.
Todays date is {self.today}. 

Call a function only if you are sure the user wants a specific tool called or you want to call for help because the topic does not concern the users calendar. Ask for more information if a task request seems to broad.
After every message decide if you want to call a function or anwser with plain text. You CANNOT do both. Call a function only if you are sure the user wants a specific tool called. Keep the conversation going until the user specifically wants to end the conversation. DON'T end the conversation to early.
Respond with the function you want to use if you decide to call a function, else respond with plain text.

Here are the different color_ids you should use:
'10' - green and music related, 
'5' - yellow and Friends related, 
'4' - light red and study related, 
'8' - grey and used when unsure",

"""
        self.messages: list[dict[str,str]] = [{
                "role": "system",
                "content": self.prompt
            }]

    def define_tools(self) -> list[str]:
        return self.tools

    def define_prompt(self) -> str:
        return self.prompt

    def get_events(self, time_from, time_till):
        try:
            service = build('calendar', 'v3', credentials=self.creds)

            # Call the Calendar API
            time_point_start = time_from if "Z" in time_from else time_from + 'Z'
            time_point_end = time_till if "Z" in time_till else time_till + 'Z'

            events_result = service.events().list(calendarId='primary', timeMin = time_point_start, timeMax = time_point_end, 
                                                    maxResults=3, singleEvents=True,
                                                    orderBy='startTime').execute()
            events = events_result.get('items', [])

            if not events:
                return []
            
            return events
            
        except Exception as error:
            print(f'An error occurred: {error}')


    def put_event(self, summary, time_from, time_till, description = None, color_id = None):
        try:
            service = build('calendar', 'v3', credentials=self.creds)

            # Call the Calendar API
            # now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            time_point_start = time_from
            time_point_end = time_till

            event = {
                'summary': summary,
                "description": description if description != None else "",
                'start': {
                    'dateTime': time_point_start,  # Adjust to your local time and format
                    'timeZone': 'Europe/Berlin',
                },
                'end': {
                    'dateTime': time_point_end,
                    'timeZone': 'Europe/Berlin',
                },
                "colorId": color_id if color_id != None else "8",
                "reminders": {
                    "useDefault": True,
                },
            }
            if description:
                event.update()
            event = service.events().insert(calendarId='primary', body=event).execute()

            return event

        except Exception as error:
            print(f'An error occurred: {error}')

    def delete_event(self, event_id):
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            service.events().delete(calendarId = 'primary', event_id = event_id).execute()
            return True
        except Exception as error:
            print(f'An error occurred: {error}')
            
    def edit_event(self, event_id, time_from = None, time_till = None, summary = None, description = None, color_id = None):
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            event = service.events().get(calendarId='primary', event_id=event_id).execute()

            start = {
                'dateTime': time_from,  # Adjust to your local time and format
                'timeZone': 'Europe/Berlin',
            } if time_from != None else event["start"]

            end = {
                'dateTime': time_till,  # Adjust to your local time and format
                'timeZone': 'Europe/Berlin',
            } if time_till != None else event["start"]

            
            event["summary"] = summary if summary != None else event["summary"]
            event["start"] = start
            event["end"] = end
            event["description"] = description if description != None else event["description"]
            event["colorId"] = color_id if color_id != None else event["colorId"]

            updated_event = service.events().update(calendarId='primary', event_id=event_id, body=event).execute()
            return updated_event
        except Exception as error:
            print(f'An error occurred: {error}')
            
    def define_function_get_events(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "get_events",
                "description": "Get information about events in the specified time slot. time_from and time_till have to be in isoformat",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_from": {"type": "string"},
                        "time_till": {"type": "string"},
                    },
                    "required": ["time_from","time_till"],
                }
            }
        }
        return function

    def define_function_put_event(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "put_event",
                "description": "Add an event with the requested information to the calendar. time_from and time_till have to be in isoformat. color_id needs suit the type of event: '10' - music related, '5' - Friends related, '4' - study related, '8' - when unsure",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "time_from": {"type": "string"},
                        "time_till": {"type": "string"},
                        "color_id": {"type": "string"},
                    },
                    "required": ["summary","time_from","time_till"],
                    # "additionalProperties": False,
                }
            }
        }
        return function

    def define_function_end_conversation(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "end_conversation",
                "description": "End the conversation, but only if it seems appropriate and the user does not have any left questions",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                }
            }
        }
        return function

    def define_function_delete_event(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "delete_event",
                "description": "Delete an existing event by providing its event_id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string"}
                    },
                    "required": ["event_id"],
                }
            }
        }
        return function

    def define_function_edit_event(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "edit_event",
                "description": "Edit an existing event by providing its event_id and attributes, that should be changed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string"},
                        "time_from": {"type": "string"},
                        "time_till": {"type": "string"},
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "color_id": {"type": "string"},
                    },
                    "required": ["event_id"],
                }
            }
        }
        return function
    
    def define_function_call_for_help(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "call_for_help",
                "description": "Call for help if you cannot help the user with their request because the topic does not concern you.",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                }
            }
        }
        return function
    

    
    def handle_function_call(self, called_function: str, arguments: dict) -> str:
        print(f"TRYING TO CALL A FUNCTION NOW ITS '{called_function}'")
        if called_function == "get_events":
            events = self.get_events(
                time_from = arguments["time_from"], 
                time_till = arguments["time_till"]
            )
            if len(events) == 0:
                return "There are no upcoming events."
            
            else:
                return f"The events for the asked time are: {events}."
            
        elif called_function == "put_event":
            print("REALLY TRYING TO PUT EVENT")
            try:
                print("REALLY TRYING TO PUT EVENT EVEN GOT INTO THE TRY")
                event = self.put_event(
                    summary = arguments["summary"], 
                    time_from = arguments["time_from"], 
                    time_till = arguments["time_till"],
                    description = arguments["description"] if "description" in arguments else None,
                    color_id = arguments["color_id"] if "color_id" in arguments else None
                )
                return f"Following event was created: {event}."
            
            except Exception as error:
                return f"The event could not be created because of {error}. Excuse yourself in front of the user."
        
        elif called_function == "delete_event":
            try:
                self.delete_event(event_id = arguments["event_id"])
                return "The event was deleted successfully"
                
            except Exception as error:
                return f"The event could not be deleted because of {error}. Excuse yourself in front of the user."
                
        elif called_function == "edit_event":
            try:
                event = self.edit_event(
                    event_id = arguments["event_id"],
                    time_from = arguments["time_from"] if "time_from" in arguments else None,
                    time_till = arguments["time_till"] if "time_till" in arguments else None,
                    summary = arguments["summary"] if "summary" in arguments else None,
                    description = arguments["description"] if "description" in arguments else None,
                    color_id = arguments["color_id"] if "color_id" in arguments else None
                )
                return f"Following event was edited: {event}."
                
            except Exception as error:
                return f"The event could not be edited because of {error}. Excuse yourself in front of the user."
        elif called_function == "call_for_help":
            self.assigned_task_to = "Manager"
            return ""
        else:
            return "Something went wrong. The function could not be called"
