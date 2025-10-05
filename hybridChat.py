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
        f"You are a tech support agent. The user sent the following message:\n"
        f"'{user_input}'\n\n"
        f"Available tools:\n{tool_list_str}\n\n"
        "Decide whether this message requires a tool or general chat.\n"
        "If it requires a tool, respond ONLY in JSON format using these tool names exactly: "
        f"{', '.join(TOOLS.keys())}\n"
        '{"tool": "TOOL_NAME", "parameters": {"param1": "value1", ...}}\n'
        "If it is general chat, respond ONLY with 'general' nothing else strictly."
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
    print("\n🔍 DEBUG - Raw model response:\n", response_str, "\n")

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
            tool_name = tool_data.get("tool")
            params = tool_data.get("parameters", {})
            
            if tool_name not in TOOLS:
                return f"⚠️ Tool '{tool_name}' not recognized."
            
            return call_tool(tool_name, params)
        #can enhance exceptioins 
        except json.JSONDecodeError:
            return "⚠️ Could not parse JSON. Please check tool request format."
        except Exception as e:
            return f"⚠️ Error executing tool: {e}"
        
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
