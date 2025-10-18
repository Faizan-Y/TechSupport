import requests
from pydantic import BaseModel, Field, ValidationError
from typing import Dict
import json
from env_config import *

logging.basicConfig(level=logging.INFO)
documents: Dict[str, str] = {}

# Tool Inputs - Pydantic Model

class UpdateDocumentInput(BaseModel):
    doc_name: str = Field(..., description="Name of the document")
    content: str = Field(..., description="Content to update")

class CancelTripInput(BaseModel):
    trip_id: str = Field(..., description="Trip ID to cancel")

class ResetPasswordInput(BaseModel):
    user: str = Field(..., description="Username for password reset")

class CancelTripAPIInput(BaseModel):
    trip_no: int = Field(..., description="Trip number to cancel")
    reason: str = Field(..., min_length=4, description="Reason for cancellation")
    usr: int = Field(USER_ID, description="User ID")
    auth_token: str = Field(AUTH_TOKEN, description="User authentication token")


def update_document_tool(input_data: UpdateDocumentInput) -> str:
    documents[input_data.doc_name] = input_data.content
    return f'Document "{input_data.doc_name}" updated successfully.'

# def cancel_trip_tool(input_data: CancelTripInput) -> str:
#     return f'Trip {input_data.trip_id} cancelled successfully.'

def reset_password_tool(input_data: ResetPasswordInput) -> str:
    logger.info(f"Password for {input_data.user} reset successfully.")
    return f'Password for {input_data.user} reset successfully.'

def cancel_trip_api_tool(input_data: CancelTripAPIInput) -> str:
    """Calls API  Mockoon simulate API"""
    url = CANCEL_TRIP_API  #
    headers = {
        "x-access-token": input_data.auth_token,
        "x-api-key": CANCEL_TRIP_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "task_code": "TRIP_CANCELLATION",
        "usr": input_data.usr,
        "meta": {
            "trip_no": input_data.trip_no,
            "reason": input_data.reason,
            "api_key": CANCEL_TRIP_API_KEY,
            "auth_token": input_data.auth_token
        }
    }
    logger.debug(f"API Request Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"API Response: {json.dumps(data, indent=2)}")
        result = data.get("result", "UNKNOWN")
        message = data.get("message", "")
        meta = data.get("meta", {})
        logger.debug(f"API Response: {json.dumps(data, indent=2)}")
        return f"[{result}] {message} | Meta: {meta}"
    except requests.exceptions.Timeout:
        logger.error("API call timed out after 5 seconds.")
        return "API call timed out after 5 seconds."
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to server at localhost:  .")
        return "Could not connect to  server at localhost:3001."
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        return f" HTTP error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        logger.exception("Unexpected error in cancel_trip_api_tool:")
        return f"Unexpected error: {e}"


TOOLS = {
    "update_document": {
        "function": update_document_tool,
        "input_model": UpdateDocumentInput,
        "description": "Update a document's content"
    },

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


# Tool Executor
def call_tool(tool_name: str, params: dict) -> str:
    if tool_name not in TOOLS:
        logger.error(f"Tool '{tool_name}' not found.")
        return f"Tool '{tool_name}' not found."

    tool = TOOLS[tool_name]
    input_model = tool["input_model"]

    try:
        validated_input = input_model(**params)
        return tool["function"](validated_input)

    except ValidationError as e:
        errors = []
        for err in e.errors():
            field = err.get("loc", ["?"])[0]
            msg = err.get("msg", "Invalid value")
            errors.append(f"{field}: {msg}")
        error_text = "; ".join(errors)
        logger.error(f"Validation failed for '{tool_name}': {error_text}")
        return f"Missing or invalid parameters for '{tool_name}': {error_text}"

    except Exception as e:
        logger.exception(f"Unexpected error in '{tool_name}':")
        return f" Unexpected error in '{tool_name}': {e}"
