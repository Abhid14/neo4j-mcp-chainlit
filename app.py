import json

from mcp import ClientSession
import anthropic

import chainlit as cl

anthropic_client = anthropic.AsyncAnthropic()
SYSTEM = """
You are a data data analyst/scientist/engineer assistant for specializing in Neo4j and Graph Databases and its features/paradigms. Your role is to help users query the Neo4j database efficiently.

INITIALIZATION:
- Before responding to the first user request, silently retrieve the Neo4j schema
- This will enable you to provide accurate query assistance

RESPONSE GUIDELINES:
- Keep responses concise to minimize token usage
- Present results in tabular format when applicable
- Include direct answers without excessive explanation

Remember that users will be relying on your expertise as an in-house data analyst/scientist/engineer, so prioritize accuracy and efficiency in your query assistance.
"""

def flatten(xss):
    return [x for xs in xss for x in xs]


@cl.on_mcp_connect
async def on_mcp(connection, session: ClientSession):
    result = await session.list_tools()
    tools = [{
        "name": t.name,
        "description": t.description,
        "input_schema": t.inputSchema,
    } for t in result.tools]

    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = tools
    cl.user_session.set("mcp_tools", mcp_tools)


@cl.step(type="tool")
async def call_tool(tool_use):
    tool_name = tool_use.name
    tool_input = tool_use.input

    current_step = cl.context.current_step
    current_step.name = tool_name

    # Identify which mcp is used
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_name = None

    for connection_name, tools in mcp_tools.items():
        if any(tool.get("name") == tool_name for tool in tools):
            mcp_name = connection_name
            break

    if not mcp_name:
        current_step.output = json.dumps(
            {"error": f"Tool {tool_name} not found in any MCP connection"})
        return current_step.output

    mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)

    if not mcp_session:
        current_step.output = json.dumps(
            {"error": f"MCP {mcp_name} not found in any MCP connection"})
        return current_step.output

    try:
        current_step.output = await mcp_session.call_tool(tool_name, tool_input)
    except Exception as e:
        current_step.output = json.dumps({"error": str(e)})

    return current_step.output


async def call_claude(chat_messages):
    msg = cl.Message(content="")
    mcp_tools = cl.user_session.get("mcp_tools", {})
    # Flatten the tools from all MCP connections
    tools = flatten([tools for _, tools in mcp_tools.items()])

    async with anthropic_client.messages.stream(
        system=SYSTEM,
        max_tokens=12024,
        messages=chat_messages,
        tools=tools,
        model="claude-3-7-sonnet-20250219",
    ) as stream:
        async for text in stream.text_stream:
            await msg.stream_token(text)

    await msg.send()
    response = await stream.get_final_message()

    return response


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Explain the ontology of the database",
            message="Explain the ontology of the database",
        ),
        cl.Starter(
            label="Create a new node",
            message="Help to create a new node in the db followed by user's requirements",
        ),
        cl.Starter(
            label="Count of total nodes and relationships",
            message="Give the total count of total nodes and relationships in the db",
        )
    ]


@cl.on_chat_start
async def on_chat_start():
    # await cl.Message(content="Good afternoon, Abhishek").send()
    cl.user_session.set("chat_messages", [])


@cl.on_message
async def on_message(msg: cl.Message):
    chat_messages = cl.user_session.get("chat_messages")
    chat_messages.append({"role": "user", "content": msg.content})
    response = await call_claude(chat_messages)

    while response.stop_reason == "tool_use":
        tool_use = next(
            block for block in response.content if block.type == "tool_use")
        tool_result = await call_tool(tool_use)

        messages = [
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(tool_result),
                    }
                ],
            },
        ]

        chat_messages.extend(messages)
        response = await call_claude(chat_messages)

    final_response = next(
        (block.text for block in response.content if hasattr(block, "text")),
        None,
    )

    chat_messages = cl.user_session.get("chat_messages")
    chat_messages.append({"role": "assistant", "content": final_response})
