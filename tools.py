
import requests
from pydantic import BaseModel, Field
from typing import Dict
import json


# dummy in-memory documents (demo)
documents: Dict[str, str] = {}
user_id = 192731
auth_token = "dummy"



# Tool Inputs
class UpdateDocumentInput(BaseModel):
    doc_name: str = Field(..., description="Name of the document")
    content: str = Field(..., description="Content to update")

class CancelTripInput(BaseModel):
    trip_id: str = Field(..., description="Trip ID to cancel")

class ResetPasswordInput(BaseModel):
    user: str = Field(..., description="Username for password reset")

class CancelTripAPIInput(BaseModel):
    trip_no: int = Field(..., description="Trip number to cancel")
    reason: str = Field(..., description="Reason for cancellation")
    usr: int = Field(user_id, description="User ID")
    auth_token: str = Field(auth_token, description="User authentication token")

# Tool Functions
def update_document_tool(input_data: UpdateDocumentInput) -> str:
    documents[input_data.doc_name] = input_data.content
    return f'Document "{input_data.doc_name}" updated successfully.'

# def cancel_trip_tool(input_data: CancelTripInput) -> str:
#     return f'Trip {input_data.trip_id} cancelled successfully.'

def reset_password_tool(input_data: ResetPasswordInput) -> str:
    return f'Password for {input_data.user} reset successfully.'

def cancel_trip_api_tool(input_data: CancelTripAPIInput) -> str:
    """Calls API  Mockoon simulate API)"""
    url = "http://localhost:3001/cancel-trip"  #
    headers = {
        "x-access-token": input_data.auth_token,
        "x-api-key": "Vq3DPSIcy0W11XQ0BUYqfw",
        "Content-Type": "application/json"
    }
    payload = {
        "task_code": "TRIP_CANCELLATION",
        "usr": input_data.usr,
        "meta": {
            "trip_no": input_data.trip_no,
            "reason": input_data.reason,
            "api_key": "Vq3DPSIcy0W11XQ0BUYqfw",
            "auth_token": input_data.auth_token
        }
    }
    # print("\n DEBUG - API Request Payload:\n", json.dumps(payload, indent=2))

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        # print("\n DEBUG - API Response:\n", json.dumps(data, indent=2))
        result = data.get("result", "UNKNOWN")
        message = data.get("message", "")
        meta = data.get("meta", {})
        return f"[{result}] {message} | Meta: {meta}"
    except requests.exceptions.Timeout:
        return "❌ API call timed out after 5 seconds."
    except requests.exceptions.ConnectionError:
        return "❌ Could not connect to Mockoon server at localhost:3001."
    except requests.exceptions.HTTPError as e:
        return f"❌ HTTP error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"⚠️ Unexpected error: {e}"

# Tool Dictonary
TOOLS = {
    "update_document": {
        "function": update_document_tool,
        "input_model": UpdateDocumentInput,
        "description": "Update a document's content"
    },
    # "cancel_trip": {
    #     "function": cancel_trip_tool,
    #     "input_model": CancelTripInput,
    #     "description": "Cancel a trip by trip ID"
    # },
    "reset_password": {
        "function": reset_password_tool,
        "input_model": ResetPasswordInput,
        "description": "Reset a user's password"
    },
    "cancel_trip_api": {
        "function": cancel_trip_api_tool,
        "input_model": CancelTripAPIInput,
        "description": "Cancel a trip via REST API with trip number, reason, user ID, and auth token"
    }
}

# Dynamic call for tools
def call_tool(tool_name: str, params: dict) -> str:
    if tool_name not in TOOLS:
        return f"Tool '{tool_name}' not found."
    # Only set defaults if not already present
    '''if tool_name == "cancel_trip_api":
        if not params.get("usr"):
            params["usr"] = int(user_id)
        if not params.get("auth_token"):
            params["auth_token"] = auth_token'''
    tool = TOOLS[tool_name]
    validated_input = tool["input_model"](**params)
    return tool["function"](validated_input)
