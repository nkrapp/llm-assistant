import os.path
from dotenv import load_dotenv
from calendarHelper.calendarHelper import CalendarHelper
import datetime
import json
import caldav
import uuid

class NextcloudCalendar(CalendarHelper):

    def __init__(self):

        with open('nextcloudCredentials.json') as f:
            d = json.load(f)
            
            self.client = caldav.DAVClient(
                url = "https://cloud.sympalog.org/remote.php/dav",
                username = d["user"],
                password = d["pass"],
            )
        
        calendars = self.client.principal().calendars()
        
        if not calendars:
            raise Exception("calendar not found")
        else:
            calendar = self.getCalendarByName(calendars, "Nikita")
            if calendar == None:
                raise Exception("calendar not found")
            else:
                self.calendar: caldav.Calendar = calendar

        self.tools = [
            # self.define_function_getEvents(),
            self.define_function_putEvents(),
            # self.define_function_deleteEvent(),
            # self.define_function_editEvent(),
            # self.define_function_endConversation(),
        ]
        
        self.today = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
        self.prompt = f"""
You are a helpful dialogue-assistant with tool calling capabilities, that allow you to access and change a calendar. Todays date is {self.today}. 

After every message decide if you want to call a function or anwser with plain text. You CANNOT do both. Keep the conversation going until the user specifically wants to end the conversation. DO NOT end the conversation to early.
Respond with the function you want to use if you decide to call a function, else respond with plain text.

If you are calling a function: Always put the object inside a list. Do not write an introduction or summary.
"""

    
    def getCalendarByName(self, calendars: list[caldav.Calendar], name: str) -> caldav.Calendar | None:
        searchedCalendar = None
        if len(calendars) > 0:
            searchedCalendar = calendars[0]
        for calendar in calendars:
            if calendar.name == name:
                searchedCalendar = calendar
                break
        return searchedCalendar
        

    def defineTools(self) -> list[str]:
        return self.tools

    def definePrompt(self) -> str:
        return self.prompt


    def putEvent(self, summary, timeFrom, timeTill, description = None):
        
        try:
            self.calendar.add_event(f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:NIKITAS_CALENDAR_ASSISTANT
BEGIN:VEVENT
UID:{uuid.uuid4()}-nikitasCustomEvents
DTSTAMP:{self.today}
DTSTART:{timeFrom}
DTEND:{timeTill}
SUMMARY:{summary} 
DESCRIPTION:{"no description" if description == None else description}
END:VEVENT
END:VCALENDAR""")
            return "Added event successfully"

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
                "description": "Add an event with the requested information to the calendar. timeFrom and timeTill have to be in iCalendar (ICS) format (YYYYMMDDTHHMMSSZ).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "timeFrom": {"type": "string"},
                        "timeTill": {"type": "string"},
                    },
                    "required": ["summary","timeFrom","timeTill"],
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
    
    def handleFunctionCall(self, calledFunction: str, arguments: dict) -> str:

        if calledFunction == "putEvent":
            try:
                self.putEvent(
                    summary = arguments["summary"], 
                    timeFrom = arguments["timeFrom"], 
                    timeTill = arguments["timeTill"],
                    description = arguments["description"] if "description" in arguments else None,
                )
                return "The event was created successfully."
            
            except Exception as error:
                return f"The event could not be created because of {error}. Excuse yourself in front of the user."
        else:
            return "The called function does not exist. DO NOT try again!"
        
                
