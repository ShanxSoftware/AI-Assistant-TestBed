"""
Test bench for the xAI Handler Library
"""
import os
import json
from typing import Optional, Dict, Callable
from pydantic import BaseModel, Field
from dotenv import load_dotenv
# Import library components
from xaihandler import (
    xAI_Handler,
    AgentPersonality, 
    Archetype, 
    AgentTrait, 
    Trait,
    StatefulMemory
)

load_dotenv()

# Simulated tool functions for testing
def check_calendar(query_date: Optional[str] = None) -> Dict:
    """Simulated calendar check tool."""
    if not query_date:
        query_date = "today"
    return {
        "date": query_date,
        "appointments": [{"time": "10:00 AM", "title": "Team Meeting"}],
        "summary": f"1 appointment on {query_date}"
    }

class CalendarParams(BaseModel):
    query_date: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD")

def calculate_math(expression: str) -> str: #: JAKOB: Grok, should this be a Dict? Check https://docs.x.ai/docs/guides/function-calling
    """Simulated math calculator tool."""
    try:
        return eval(expression)  # For demo only; use safe eval in production
    except Exception as e:
        return f"Error: {str(e)}"

class MathParams(BaseModel):
    expression: str = Field(description="Math expression to evaluate")

def get_weather_station_results(isoDateString: Optional[str] = None) -> Dict: 
    isoDateString = "2025-09-29" if not isoDateString else isoDateString
    return {
        "Date": isoDateString,
        "Location": "Boolboonda, QLD", 
        "Lat": -25.053116,
        "Long": 151.653333,
        "Mean Air Pressure (mb)": 700,
        "Max Temp (C)": 35,
        "Min Temp (C)": 16,
        "Wind Dir.": 200,
        "Wind Speed (km/h)": 8,
        "Humidity (%)": 60,
        "Rain (mL)": 20
    }

class WeatherParams(BaseModel): 
    isoDateString: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD")

# Available simulated tools
SIMULATED_TOOLS = {
    "check_calendar": (check_calendar, CalendarParams, "Check calendar for appointments"),
    "calculate_math": (calculate_math, MathParams, "Evaluate math expressions"),
    "get_weather_station_results": (get_weather_station_results, WeatherParams, "Retrieve weather station data for a given date.")
}

# Personality presets
PERSONALITY_PRESETS = {
    "alex": AgentPersonality(
        name="Alex",
        gender="female",
        primary_archetype=Archetype.AMIABLE,
        primary_weight=0.6,
        secondary_archetype=Archetype.EXPRESSIVE,
        job_description="Personal assistant",
        traits=[
            AgentTrait(trait=Trait.EMPATHY, intensity=60),
            AgentTrait(trait=Trait.CURIOSITY, intensity=50),
            AgentTrait(trait=Trait.PRECISION, intensity=90)
        ]
    ),
    "bob": AgentPersonality(
        name="Bob",
        gender="male",
        primary_archetype=Archetype.ANALYTICAL,
        primary_weight=0.7,
        secondary_archetype=Archetype.DRIVER,
        job_description="Technical advisor",
        traits=[
            AgentTrait(trait=Trait.PRECISION, intensity=90),
            AgentTrait(trait=Trait.CONFIDENCE, intensity=80),  # Replaced "logic" with CONFIDENCE (assuming closest match; adjust if needed)
            AgentTrait(trait=Trait.RESPONSIVENESS, intensity=70)  # Replaced "efficiency" with RESPONSIVENESS; adjust based on your Trait enum
        ]
    )
}

def load_test_batteries(directory: str = "test_batteries") -> Dict[str, list]:
    """Load JSON test batteries from a directory."""
    batteries = {}
    if not os.path.exists(directory):
        os.makedirs(directory)
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), "r") as f:
                battery_name = filename.replace(".json", "")
                batteries[battery_name] = json.load(f)["tests"]
    return batteries

def run_test(handler: xAI_Handler, test_case: dict) -> bool:
    """Run a single test case and check if it passes."""
    # Register specified tools for this test
    for tool_name in test_case.get("tools", []):
        if tool_name in SIMULATED_TOOLS:
            func, param_model, desc = SIMULATED_TOOLS[tool_name]
            handler.add_tool(tool_name, func, param_model, desc)

    # Send input and get response
    resp = handler.chat(test_case["input"])
    print(f"running {test_case["input"]}")

    # Check if expected output is in response (simple substring match for demo)
    passed = test_case["expected"].lower() in resp["content"].lower()

    # Clean up tools
    for tool_name in test_case.get("tools", []):
        handler.remove_tool(tool_name)

    return passed

def display_results(results: list):
    """Display test results in a table format."""
    print("| Test # | Test Name          | Passed/Failed |")
    print("|--------|--------------------|--------------|")
    for idx, (test_name, passed) in enumerate(results, 1):
        status = "Passed" if passed else "Failed"
        print(f"| {idx:<6} | {test_name:<18} | {status:<12} |")

def manual_chat(handler: xAI_Handler):
    """Manual direct chat mode with the selected personality."""
    print("\nEntering manual chat mode. Type 'exit' to quit.")
    session_id = "manual_session"
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        resp = handler.chat(user_input, session_id=session_id)
        print(f"Assistant: {resp['content']}")

def main():
    # Initialize handler
    api_key = os.getenv("XAI_API_KEY")
    if not api_key: 
        raise ValueError("XAI_API_KEY missing in .env")
    handler = xAI_Handler(api_key=api_key, validate_connection=False)

    # Menu: Select personality preset
    print("\nAvailable Personality Presets:")
    preset_names = list(PERSONALITY_PRESETS.keys())
    for i, name in enumerate(preset_names, 1):
        print(f"{i}. {name.capitalize()}")
    choice = int(input("Select personality (number): ")) - 1
    selected_personality = PERSONALITY_PRESETS[preset_names[choice]]
    handler.config.personality = selected_personality
    print(f"Selected: {selected_personality.name}")

    # Load test batteries
    batteries = load_test_batteries()
    if not batteries:
        print("No test batteries found. Create JSON files in 'test_batteries/' directory.")
        print("Example JSON structure: {'tests': [{'name': 'Test1', 'input': 'Hello', 'expected': 'hello', 'tools': []}]}")
        return

    # Menu: Select test battery
    print("\nAvailable Test Batteries:")
    battery_names = list(batteries.keys())
    for i, name in enumerate(battery_names, 1):
        print(f"{i}. {name}")
    choice = int(input("Select battery (number): ")) - 1
    selected_battery = batteries[battery_names[choice]]

    # Run tests and collect results
    results = []
    for test_case in selected_battery:
        passed = run_test(handler, test_case)
        results.append((test_case["name"], passed))

    # Display results
    display_results(results)

    # Option for manual mode
    manual = input("\nEnter manual chat mode? (y/n): ").lower() == 'y'
    if manual:
        manual_chat(handler)

if __name__ == "__main__":
    main()