import os.path
from dotenv import load_dotenv
from assistants.managerStructure import ManagerStructure
import datetime
import json
import caldav
import uuid

class NextcloudCalendar(ManagerStructure):

    def __init__(self):
        super().__init__()

        with open('nextcloudCredentials.json') as f:
            d = json.load(f)
            
            self.client = caldav.DAVClient(
                url = "https://cloud.sympalog.org/remote.php/dav",
                username = d["login"],
                password = d["pass"],
            )
            self.calendar_name = d["calendar_name"]
        
        calendars = self.client.principal().calendars()
        
        if not calendars:
            raise Exception("calendar not found")
        else:
            calendar = self.get_calendar_by_name(calendars, self.calendar_name)
            if calendar == None:
                raise Exception("calendar not found")
            else:
                self.calendar: caldav.Calendar = calendar

        for tool in [
            self.define_function_get_events(),
            self.define_function_put_event(),
        ]:
            self.tools.append(tool)
        
        self.today = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
        self.prompt = f"""You are a helpful dialogue-assistant with tool calling capabilities, that allow you to access and change a calendar. 
Have a pleasant conversation with the user and try to help them with their tasks.
        
Todays date is {self.today}. 

Call a function only if you are sure the user wants a specific tool called. Ask for more information if a task request seems to broad.
After every message decide if you want to call a function or anwser with plain text. You CANNOT do both. Keep the conversation going until the user specifically wants to end the conversation. DO NOT end the conversation to early.
Respond with the function you want to use if you decide to call a function, else respond with plain text.

If you are calling a function: Always put the object inside a list. Do not write an introduction or summary.
"""

    
    def get_calendar_by_name(self, calendars: list[caldav.Calendar], name: str) -> caldav.Calendar | None:
        searchedCalendar = None
        if len(calendars) > 0:
            searchedCalendar = calendars[0]
        for calendar in calendars:
            if calendar.name == name:
                searchedCalendar = calendar
                break
        return searchedCalendar
        

    def define_tools(self) -> list[str]:
        return self.tools

    def define_prompt(self) -> str:
        return self.prompt

    def get_events(self, time_from, time_till):
        print(f"searching from {time_from} until {time_till}")
        events = self.calendar.date_search(start = time_from, end = time_till)
        print(f"returned events are {events}")
        result_events = []
        for (index, event) in enumerate(events):
            vevent = event.vobject_instance.vevent
            print(f"vevent is: {vevent}")
            summary = vevent.summary.value if hasattr(vevent, 'summary') else "No title"
            print(f"summary in vevent is: {summary}")
            dtstart = vevent.dtstart.value if hasattr(vevent, 'dtstart') else "Unknown start time"
            dtend = vevent.dtend.value if hasattr(vevent, 'dtend') else "Unknown end time"
            result_events.append(f"Event-{index}: summary is '{summary}' and from {dtstart} until {dtend}")
        return result_events

    def put_event(self, summary, time_from, time_till, description = None):
        
        try:
            self.calendar.add_event(f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:NIKITAS_CALENDAR_ASSISTANT
BEGIN:VEVENT
UID:{uuid.uuid4()}-nikitasCustomEvents
DTSTAMP:{self.today}
DTSTART:{time_from}
DTEND:{time_till}
SUMMARY:{summary} 
DESCRIPTION:{"no description" if description == None else description}
END:VEVENT
END:VCALENDAR""")
            return "Added event successfully"

        except Exception as error:
            print(f'An error occurred: {error}')

            
    def define_function_get_events(self) -> dict:
        function = {
            "type": "function",
            "function": {
                "name": "get_events",
                "description": "Get information about events in the specified time slot. time_from and time_till have to be in isoformat.",
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
                "description": "Add an event with the requested information to the calendar. time_from and time_till have to be in iCalendar (ICS) format (YYYYMMDDTHHMMSSZ).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "time_from": {"type": "string"},
                        "time_till": {"type": "string"},
                    },
                    "required": ["summary","time_from","time_till"],
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
    
    def handle_function_call(self, called_function: str, arguments: dict) -> str:

        if called_function == "put_event":
            try:
                self.put_event(
                    summary = arguments["summary"], 
                    time_from = arguments["time_from"], 
                    time_till = arguments["time_till"],
                    description = arguments["description"] if "description" in arguments else None,
                )
                return "The event was created successfully."
            
            except Exception as error:
                return f"The event could not be created because of {error}. Excuse yourself in front of the user."
            
        elif called_function == "get_events":
            try:
                events = self.get_events(
                    time_from = arguments["time_from"], 
                    time_till = arguments["time_till"],
                )
                return f"Following events were found: {events}."
            
            except Exception as error:
                return f"Events could not be found because of {error}. Excuse yourself in front of the user."
            
        else:
            return "The called function does not exist. DO NOT try again!"
        
                
