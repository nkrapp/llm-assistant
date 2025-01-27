import os
import os.path
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# colorIds:
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


class CalendarHelper:

    def __init__(self):
        
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

        self.tools = [
            self.define_function_getEvents(),
            self.define_function_putEvents(),
            self.define_function_deleteEvent(),
            self.define_function_editEvent(),
            # self.define_function_endConversation(),
        ]

    def defineTools(self) -> list[str]:
        return self.tools

    def getEvents(self, timeFrom, timeTill):
        try:
            service = build('calendar', 'v3', credentials=self.creds)

            # Call the Calendar API
            timePointStart = timeFrom if "Z" in timeFrom else timeFrom + 'Z'
            timePointEnd = timeTill if "Z" in timeTill else timeTill + 'Z'

            events_result = service.events().list(calendarId='primary', timeMin = timePointStart, timeMax = timePointEnd, 
                                                    maxResults=3, singleEvents=True,
                                                    orderBy='startTime').execute()
            events = events_result.get('items', [])

            if not events:
                return []
            
            return events
            
        except Exception as error:
            print(f'An error occurred: {error}')


    def putEvent(self, summary, timeFrom, timeTill, description = None, colorId = None):
        try:
            service = build('calendar', 'v3', credentials=self.creds)

            # Call the Calendar API
            # now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            timePointStart = timeFrom
            timePointEnd = timeTill


            print("inside calendar putEvent")
            event = {
                'summary': summary,
                "description": description if description != None else "",
                'start': {
                    'dateTime': timePointStart,  # Adjust to your local time and format
                    'timeZone': 'Europe/Berlin',
                },
                'end': {
                    'dateTime': timePointEnd,
                    'timeZone': 'Europe/Berlin',
                },
                "colorId": colorId if colorId != None else "8",
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

    def deleteEvent(self, eventId):
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            service.events().delete(calendarId = 'primary', eventId = eventId).execute()
            return True
        except Exception as error:
            print(f'An error occurred: {error}')
            
    def editEvent(self, eventId, timeFrom = None, timeTill = None, summary = None, description = None, colorId = None):
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            event = service.events().get(calendarId='primary', eventId=eventId).execute()

            start = {
                'dateTime': timeFrom,  # Adjust to your local time and format
                'timeZone': 'Europe/Berlin',
            } if timeFrom != None else event["start"]

            end = {
                'dateTime': timeTill,  # Adjust to your local time and format
                'timeZone': 'Europe/Berlin',
            } if timeTill != None else event["start"]

            
            event["summary"] = summary if summary != None else event["summary"]
            event["start"] = start
            event["end"] = end
            event["description"] = description if description != None else event["description"]
            event["colorId"] = colorId if colorId != None else event["colorId"]

            updated_event = service.events().update(calendarId='primary', eventId=eventId, body=event).execute()
            return updated_event
        except Exception as error:
            print(f'An error occurred: {error}')
            
    def define_function_getEvents(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "getEvents",
                "description": "Get information about events in the specified time slot. timeFrom and timeTill have to be in isoformat",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timeFrom": {"type": "string"},
                        "timeTill": {"type": "string"},
                    },
                    "required": ["timeFrom","timeTill"],
                }
            }
        }
        return function

    def define_function_putEvents(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "putEvent",
                "description": "Add an event with the requested information to the calendar. timeFrom and timeTill have to be in isoformat. colorId needs suit the type of event: '10' - music related, '5' - Friends related, '4' - study related, '8' - when unsure",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "timeFrom": {"type": "string"},
                        "timeTill": {"type": "string"},
                        "colorId": {"type": "string"},
                    },
                    "required": ["summary","timeFrom","timeTill"],
                    # "additionalProperties": False,
                }
            }
        }
        return function

    def define_function_endConversation(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "endConversation",
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

    def define_function_deleteEvent(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "deleteEvent",
                "description": "Delete an existing event by providing its eventId",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "eventId": {"type": "string"}
                    },
                    "required": ["eventId"],
                }
            }
        }
        return function

    def define_function_editEvent(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "editEvent",
                "description": "Edit an existing event by providing its eventId and attributes, that should be changed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "eventId": {"type": "string"},
                        "timeFrom": {"type": "string"},
                        "timeTill": {"type": "string"},
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "colorId": {"type": "string"},
                    },
                    "required": ["eventId"],
                }
            }
        }
        return function

