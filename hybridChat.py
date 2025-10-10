# hybrid_chat.py
import asyncio
import json
from hybridTech_support_agent import perplexity_agent, openai_agent
from pydantic_ai import ModelMessage, RunUsage
from tools import TOOLS, call_tool

# Keep conversation history per user
conversation_history: dict[str, list[ModelMessage]] = {}

for name, tool in TOOLS.items():
    func = tool["function"]
    print(f"Tool: {name} | Type: {type(func)} | Callable: {callable(func)}")

async def hybrid_controller(user_id: str, user_input: str, usage: RunUsage):
    """
    Hybrid controller that explicitly provides available tools to the agent.
    The agent decides if this is a tool request or general chat.
    """
    #tool list for better classification
    tool_list_str = "\n".join([f"{name}: {tool['description']}" for name, tool in TOOLS.items()])

    #for classification + tool selection
    prompt = (
        f"You are a strict tech support assistant.\n"
        f"The user said:\n'{user_input}'\n\n"
        f"Available tools:\n{tool_list_str}\n\n"
        "Your task:\n"
        "- Decide whether this message requires a tool or is general chat.\n"
        "- If it requires a tool, respond ONLY in strict JSON format:\n"
        '  {\"tool\": \"TOOL_NAME\", \"parameters\": {\"param1\": \"value1\", ...}}\n\n'
        "🚫 NEVER assume or invent any parameter values.\n"
        "If a required parameter is missing or unclear, respond ONLY with:\n"
        '  {\"missing_parameter\": \"name_of_parameter\"}\n\n'
        "If the user is just chatting, respond ONLY with:\n"
        '  \"general\"\n'

        # f"You are a tech support agent. The user sent the following message:\n"
        # f"'{user_input}'\n\n"
        # f"Available tools:\n{tool_list_str}\n\n"
        # "Decide whether this message requires a tool or general chat.\n"
        # "If it requires a tool, respond ONLY in JSON format using these tool names exactly: "
        # f"{', '.join(TOOLS.keys())}\n"
        # "⚠️ IMPORTANT:\n"
        # "- NEVER invent or assume any parameter value.\n"
        # "- If any required parameter is missing, respond ONLY with:\n"
        # '{"missing_parameter": "name_of_parameter"}\n'
        # "Do not make up placeholders like 'No reason provided'."
        # '{"tool": "TOOL_NAME", "parameters": {"param1": "value1", ...}}\n'
        # "If it is general chat, respond ONLY with 'general' nothing else strictly."
    )

    # Asking agent (HybridToolAgent) for decision / we can use keywords too clasify
    ''' 
    if any(word in user_input.lower() for word in ["cancel", "update", "reset"]):
        assume tool request
    else:
        general chat
    '''

    result = await openai_agent.run(
        prompt,
        message_history=conversation_history.get(user_id),
        usage=usage
    )
    # response_str = str(result).strip()
    response_str = getattr(result, "output", str(result)).strip()
    print("\nDEBUG - unprocessed response:\n", response_str, "\n")

    if response_str.lower() == "general":
        # General chat handled by Perplexity agent
        chat_result = await perplexity_agent.run(
            user_input,
            message_history=conversation_history.get(user_id),
            usage=usage
        )
        return str(chat_result)
    else:
        # Tool execution
        try:
            tool_data = json.loads(response_str)

            # Handle missing parameter case first
            if "missing_parameter" in tool_data:
                missing_param = tool_data["missing_parameter"]
                return f"⚠️ I need the '{missing_param}' to continue. Please provide it along with other parameters too."

            tool_name = tool_data.get("tool")
            params = tool_data.get("parameters", {})

            if tool_name not in TOOLS:
                return f"⚠️ Tool '{tool_name}' not recognized."


            validated_input = TOOLS[tool_name]["input_model"](**params)
            # Now missing fields can be checked like this:
            missing_fields = [
                field for field, value in validated_input.model_dump().items()
                if value in [None, "", "unknown", "User requested cancellation"]
            ]

            # If the model still invents missing params, catch them at runtime
            # missing_fields = [
            #     field for field in TOOLS[tool_name]["input_model"].model_fields.keys()
            #     if field not in params or params[field] in [None, "", "unknown", "User requested cancellation"]
            # ]
            if missing_fields:
                return f"⚠️ Missing parameters: {', '.join(missing_fields)}. Please provide them."

            return call_tool(tool_name, params)

        except json.JSONDecodeError:
            return "⚠️ Could not parse JSON. Please check tool request format."
        except Exception as e:
            return f"⚠️ Error executing tool: {e}"
        finally:
            print(f"✅ Finished processing for user={user_id} | input='{user_input}'")

        
async def main():
    print(" Hybrid Terminal Chat (type 'exit' to quit)")
    user_id = input("Enter your user ID: ").strip() or "user1"
    usage = RunUsage()
    conversation_history[user_id] = []

    while True:
        user_input = input(f"{user_id}: ").strip()
        if user_input.lower() == "exit":
            print("👋 Byee!")
            break

        reply = await hybrid_controller(user_id, user_input, usage)
        print("Agent:", reply)

        # Save conversation for context
        conversation_history[user_id].append({"role": "user", "content": user_input})
        conversation_history[user_id].append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    asyncio.run(main())
