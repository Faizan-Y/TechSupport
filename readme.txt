--> Dependencies

* install requests pydantic pydantic-ai
* export api keys PERPLEXITY_API_KEY & OPENAI_API_KEY



--> How to start the chat ?

* execute hybridChat for the chat terminal 



--> What happens when you execute?

1. User Input – The user types a command or chat message.
2. Hybrid Controller – Determines if the input is a tool request or general chat.
3. 
* Tool Request –
    The controller validates the input using Pydantic models (e.g., CancelTripAPIInput, UpdateDocumentInput) to ensure required fields are present and correctly typed.
    Calls the appropriate Python function (cancel_trip_api, update_document, etc.).
    If it’s an API tool, sends a request to the Mockoon API.
  
* General Chat – Forwarded to Perplexity AI for conversational response.

4. Response – The agent returns either the tool output or general chat response back to the user.




--> How do i add a new tool to existing flow?

1. Define your function and return result in tools.py

2. Add the tool to the TOOLS dictionary in tools.py
TOOLS["my_new_tool"] = {
    "function": my_new_tool,
    "description": "This tool processes param1 and param2 and returns a result."
}







 




