import asyncio
import json
from pydantic_ai import ModelMessage, RunUsage
from tools import TOOLS, call_tool
from tech_support_agent import create_agents
from env_config import *

conversation_history: dict[str, list[ModelMessage]] = {}
user_memo: dict[str, dict] = {}

try:
    perplexity_agent, openai_agent = create_agents()
    # logger.info(" Agents created successfully and ready for use.")
except Exception as e:
    logger.exception(f"❌ Agent creation failed: {e}")

async def hybrid_controller(user_id: str, user_input: str, usage: RunUsage):
    tool_list_str = "\n".join([f"{name}: {tool['description']}" for name, tool in TOOLS.items()])

    prompt = (
        f"You are a strict tech support assistant that never assume's parameter or feilds value if not given.\n"
        f"The user said:\n'{user_input}'\n\n"
        f"Available tools:\n{tool_list_str}\n\n"
        "Your task:\n"
        "- Decide whether this message requires a tool or is general chat.\n"
        "- If it requires a tool, never assume parameter or feilds value if not given and respond ONLY in strict JSON format:\n"
        '  {\"tool\": \"TOOL_NAME\", \"parameters\": {\"param1\": \"value1\", ...}}\n\n'
        "If the user is just chatting, respond ONLY with:\n"
        '  "general"\n'
    )

    result = await openai_agent.run(
        prompt,
        message_history=conversation_history.get(user_id),
        usage=usage
    )
    response_str = getattr(result, "output", str(result)).strip()
    logger.debug(f"DEBUG - unprocessed response:\n{response_str}")

    if not response_str or response_str.lower() == "general" or not response_str.startswith("{"):
        if user_id in user_memo:
            memo = user_memo[user_id]
            tool_name = memo.get("tool")
            params = memo.get("parameters", {})
            missing_param = None
            for field, value in params.items():
                if value in [None, "", "unknown", "User requested cancellation"]:
                    missing_param = field
                    break
            if missing_param:
                params[missing_param] = user_input
                validated_input = TOOLS[tool_name]["input_model"](**params)
                missing_fields = [
                    f for f, v in validated_input.model_dump().items()
                    if v in [None, "", "unknown", "User requested cancellation"]
                ]
                if missing_fields:
                    user_memo[user_id]["parameters"] = params
                    return f"⚠️ Missing parameters: {', '.join(missing_fields)}. Please provide them."
                result = call_tool(tool_name, params)
                del user_memo[user_id]
                return result
        # fallback to general chat
        chat_result = await perplexity_agent.run(
            user_input,
            message_history=conversation_history.get(user_id),
            usage=usage
        )
        return str(chat_result)


    try:
        tool_data = json.loads(response_str)

        if "missing_parameter" in tool_data:
            missing_param = tool_data["missing_parameter"]
            if user_id in user_memo:
                tool_name = user_memo[user_id].get("tool")
                if tool_name:
                    return f"⚠️ I still need '{missing_param}' for '{tool_name}'. Please provide it."
            return f"⚠️ I need the '{missing_param}' to continue. Please provide it."

        tool_name = tool_data.get("tool")
        params = tool_data.get("parameters", {})

        if tool_name not in TOOLS:
            return f"⚠️ Tool '{tool_name}' not recognized."

        if user_id in user_memo and user_memo[user_id].get("tool") == tool_name:
            prev_params = user_memo[user_id].get("parameters", {})
            params = {**prev_params, **params}

        validated_input = TOOLS[tool_name]["input_model"](**params)
        missing_fields = [
            field for field, value in validated_input.model_dump().items()
            if value in [None, "", "unknown", "User requested cancellation"]
        ]

        if missing_fields:
            user_memo[user_id] = {"tool": tool_name, "parameters": params}
            return f"⚠️ Missing parameters: {', '.join(missing_fields)}. Please provide them."

        result = call_tool(tool_name, params)
        if user_id in user_memo:
            del user_memo[user_id]
        return result

    except json.JSONDecodeError:
        logger.error(f"JSON parsing error for user {user_id} input: {user_input}")
        return "⚠️ Could not parse JSON. Please check tool request format."
    except Exception as e:
        from pydantic import ValidationError
        if isinstance(e, ValidationError):
            errors = []
            for err in e.errors():
                field = err.get("loc", ["?"])[0]
                msg = err.get("msg", "Invalid value")
                errors.append(f"{field}: {msg}")
            error_text = "; ".join(errors)
            try:
                tool_data = json.loads(response_str)
                tool_name = tool_data.get("tool")
                params = tool_data.get("parameters", {})
                user_memo[user_id] = {"tool": tool_name, "parameters": params}
            except Exception:
                pass
            logger.error(f"Validation error: {error_text}")
            return f"⚠️ Missing or invalid parameters: {error_text}"
        else:
            return f"⚠️ Error executing tool: {e}"
    finally:
        logger.info(f"✅ Finished processing for user={user_id} | input='{user_input}'")


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

        conversation_history[user_id].append({"role": "user", "content": user_input})
        conversation_history[user_id].append({"role": "assistant", "content": reply})

if __name__ == "__main__":
    asyncio.run(main())
