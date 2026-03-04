from google import genai
from google.genai import types
from PIL import Image

client = genai.Client()

# Define the tools that the assistant can use, along with their parameters
tools = [
    types.Tool(function_declarations=[

        # Tool 1: Add a calendar event
        types.FunctionDeclaration(
            name="add_event",
            description="Add calendar event",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"}
                },
                "required": ["title", "date", "time"]
            }
        ),

        # Tool 2: Set a reminder
        types.FunctionDeclaration(
            name="set_reminder",
            description="Set reminder",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"}
                },
                "required": ["text", "date", "time"]
            }
        ),

        # Tool 3: Get weather for a city
        types.FunctionDeclaration(
            name="get_weather",
            description="Get weather for city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        ),

        # Tool 4: Add a task to the to-do list
        types.FunctionDeclaration(
            name="add_task",
            description="Add a task",
            parameters={
                "type": "object",
                "properties": {
                    "task": {"type": "string"}
                },
                "required": ["task"]
            }
        ),

        # Tool 5: Draft an email
        types.FunctionDeclaration(
            name="draft_email",
            description="Draft email",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {"type": "string"},
                    "subject": {"type": "string"},
                    "topic": {"type": "string"}
                },
                "required": ["recipient", "subject", "topic"]
            }
        ),

        # Tool 6: Analyze an uploaded image
        types.FunctionDeclaration(
            name="analyze_image",
            description="Analyze uploaded image",
            parameters={"type": "object", "properties": {}}
        ),

        # Tool 7: Generate an image from a text prompt
        types.FunctionDeclaration(
            name="generate_image",
            description="Generate image from prompt",
            parameters={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"}
                },
                "required": ["prompt"]
            }
        ),

        

    ])
]



# Execute the requested tool with the provided arguments
def run_tool(name, args):
    """
    Executes the specified tool with the given arguments.
    
    Args:
        name (str): The name of the tool to execute
        args (dict): The arguments to pass to the tool
    
    Returns:
        str: Result or status message from the tool execution
    """
    

    if name == "generate_image":
        prompt = args['prompt']
        response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[prompt],
)

        for part in response.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                image = part.as_image()
                image.save("generated_image.png")

    
    elif name == "add_event":
        return f"✓ Event '{args['title']}' added for {args['date']} at {args['time']}"
    
    elif name == "set_reminder":
        return f"✓ Reminder set: '{args['text']}' on {args['date']} at {args['time']}"
    
    elif name == "get_weather":
        return f"✓ Weather for {args['city']}: Cloudy, 60°F"
    
    elif name == "add_task":
        return f"✓ Task added: '{args['task']}'"
    
    elif name == "draft_email":
        return f"✓ Email drafted to {args['recipient']} with subject '{args['subject']}' about {args['topic']}"
    
    



# Main function that sends a message to Gemini and handles tool calls
def ask_assistant(message, image_path=None):
    """
    Sends a message to Gemini and handles any tool calls it makes.
    
    Args:
        message (str): The user's message/prompt
        image_path (str, optional): Path to an image file to analyze
    """
    
    # Initialize the content list (messages / images)
    contents = []

    # If an image was provided, load it and add it to the content
    if image_path:
        with open(image_path, "rb") as f:
            contents.append(
                types.Part.from_bytes(
                    data=f.read(),
                    mime_type="image/jpeg"
                )
            )

    # Add the user's text message to the content
    contents.append(message)

    # Send the request to Gemini with the available tools
    response = client.models.generate_content(
        model="gemini-3-flash-preview",  
        contents=contents,  # The message/image to process
        config=types.GenerateContentConfig(tools=tools)  # Available tools
    )

    # Wrap in try/except to handle any errors
    try:
        # Get the first candidate response from Gemini
        candidate = response.candidates[0]
        
        # Safety check: ensure the response contains parts
        if not candidate.content.parts:
            print("No response parts")
            return
        
        # Get the first part of the response
        part = candidate.content.parts[0]
        
        # Check if Gemini decided to call a function/tool
        if hasattr(part, 'function_call') and part.function_call:
            fc = part.function_call
            # Execute the tool that Gemini requested
            result = run_tool(fc.name, fc.args)
            print(result)
        # Otherwise, if it's a text response, print the text
        elif hasattr(part, 'text'):
            print(part.text)
        else:
            # Handle unexpected response formats
            print("Unexpected response format")
    except Exception as e:
        # Catch and print any errors that occur
        print(f"Error: {e}")




#ask_assistant("Add a meeting with Sarah tomorrow at 3PM")
#ask_assistant("Remind me to call John on Friday at noon")
#ask_assistant("What is the weather today in Athens, Ohio?")
#ask_assistant("Add assignment to my to-do list: Finish the project proposal")
#ask_assistant("Create an email draft to Emily about the upcoming conference, with the subject 'Conference Details' and the topic 'Provide information about the conference schedule and location.'")
#ask_assistant("What do you see in this image?", image_path="desk.jpg")
#ask_assistant("Generate an image of a futuristic car in a cityscape")

print("Personal assistant is ready to help you with your tasks!")
print("(Use 'message | image_path.jpg' to analyze an image)\n")

while True:
    user_input = input("Enter your request (or 'quit' to exit): ")
    if user_input.lower() == "quit":
        break
    
    # Check if user provided an image path with pipe separator
    if "|" in user_input:
        message, image = user_input.split("|", 1)
        ask_assistant(message, image_path=image.strip())
    else:
        ask_assistant(user_input)
