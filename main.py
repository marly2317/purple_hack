from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from agent import ShoppingAssistant
from helper import create_tool_node_with_fallback, _print_event
from datetime import datetime
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
import uuid

import time
from langchain_core.messages import ToolMessage

# Set up the language model for the assistant
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Import your shopping tools
from tools import (
    fetch_product_info,
    fetch_recommendations,
    add_to_cart,
    remove_from_cart,
    view_checkout_info,
    get_delivery_estimate,
    get_payment_options,
)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

llm = model = ChatOllama(model = "llama3.2")

# Define the primary prompt template for the shopping assistant
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful shopping assistant. "
            "Use the available tools to answer product queries, recommend items, "
            "manage the shopping cart, and provide checkout information, delivery times, "
            "and payment options. Be clear and friendly in your responses."
            "Always ensure that any product, availability, or price information comes from the database, "
            "so the user receives the most up-to-date and reliable information. "
            "When searching for products or recommendations, if the first search returns no results, try broadening the search criteria "
            "to find relevant items. However, avoid guessing when database information is required."
            "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

# Bind the assistant tools
tools_no_confirmation = [
    fetch_product_info,
    fetch_recommendations,
    view_checkout_info,
    get_delivery_estimate,
    get_payment_options,
]

tools_need_confirmation = [
    add_to_cart,
    remove_from_cart,
]

confirmation_tool_names = {t.name for t in tools_need_confirmation}

assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    tools_no_confirmation + tools_need_confirmation
)

# Initialize the assistant with the runnable
shopping_assistant = ShoppingAssistant(assistant_runnable)

builder = StateGraph(State)

# # Define nodes: these do the work
# builder.add_node("assistant", ShoppingAssistant(assistant_runnable))
# builder.add_node("tools", create_tool_node_with_fallback(tools_list))
# # Define edges: these determine how the control flow moves
# builder.add_edge(START, "assistant")
# builder.add_conditional_edges(
#     "assistant",
#     tools_condition,
# )
# builder.add_edge("tools", "assistant")

builder.add_node("assistant", ShoppingAssistant(assistant_runnable))
builder.add_node("tools_no_confirmation", create_tool_node_with_fallback(tools_no_confirmation))
builder.add_node("tools_need_confirmation", create_tool_node_with_fallback(tools_need_confirmation))

def route_tools(state: State):
    next_node = tools_condition(state)
    # If no tools are invoked, return to the user
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    # This assumes single tool calls. To handle parallel tool calling, you'd want to
    # use an ANY condition
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in confirmation_tool_names:
        return "tools_need_confirmation"
    return "tools_no_confirmation"

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant", route_tools, ["tools_no_confirmation", "tools_need_confirmation", END]
)
builder.add_edge("tools_no_confirmation", "assistant")
builder.add_edge("tools_need_confirmation", "assistant")

# this is a complete memory for the entire graph.
memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["tools_need_confirmation"],
)

try:
    # Generate the image and save it to a file
    image_data = graph.get_graph(xray=True).draw_mermaid_png()
    with open("graph_output.png", "wb") as f:
        f.write(image_data)
    print("Image saved as graph_output.png")
except Exception as e:
    print("An error occurred:", e)
    pass


# # Example questions a user might ask the shopping assistant
tutorial_questions = [
    "Hello, can you show me the Essence Mascara Lash Princess?",
    "I'm interested in adding it to my cart.",
    "Do you have any recommendations similar to the one in my cart?",
    "What's the total price of items in my cart?",
    "Can you give me the estimated delivery time for my order?",
    "What payment options are available?",
    "I'd like to remove the that from my cart.",
    "Could you help me checkout?",
]

# Set up a unique session ID for tracking the conversation
thread_id = str(uuid.uuid4())

# Configuration tailored for the shopping assistant
config = {
    "configurable": {
        "user_id": thread_id,
        "thread_id": thread_id,
    }
}

_printed = set()

print("Welcome to the shopping assistant! Type your question below (or type 'exit' to end):")

# Start an interactive loop for user questions
while True:
    # Prompt the user to type a question
    question = input("You: ")
    
    # Break the loop if the user types 'exit'
    if question.lower() == 'exit':
        print("Ending session. Thank you for using the shopping assistant!")
        break
    
    # Stream the assistant's response for the current question
    events = graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )
    
    # Print each event response from the assistant
    for event in events:
        _print_event(event, _printed)
    
    # Get the graph state after processing the question
    snapshot = graph.get_state(config)
    
    # Handle any interrupts (like adding/removing items) that need confirmation
    while snapshot.next:
        try:
            user_input = input(
                "Are you sure about that? Type 'y' to continue;"
                " otherwise, explain your requested changed.\n\n"
            )
        except:
            user_input = "y"
        if user_input.strip() == "y":
            # Just continue
            result = graph.invoke(
                None,
                config,
            )
            print("Successfully!")
        else:
            # Satisfy the tool invocation by
            # providing instructions on the requested changes / change of mind
            result = graph.invoke(
                {
                    "messages": [
                        ToolMessage(
                            tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                            content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                        )
                    ]
                },
                config,
            )
        snapshot = graph.get_state(config)

# # We can reuse the tutorial questions from part 1 to see how it does.
# for question in tutorial_questions:
#     events = graph.stream(
#         {"messages": ("user", question)}, config, stream_mode="values"
#     )
#     for event in events:
#         _print_event(event, _printed)
#     snapshot = graph.get_state(config)
#     while snapshot.next:
#         # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
#         # Note: This code is all outside of your graph. Typically, you would stream the output to a UI.
#         # Then, you would have the frontend trigger a new run via an API call when the user has provided input.
#         try:
#             user_input = input(
#                 "Do you approve of the above actions? Type 'y' to continue;"
#                 " otherwise, explain your requested changed.\n\n"
#             )
#         except:
#             user_input = "y"
#         if user_input.strip() == "y":
#             # Just continue
#             result = graph.invoke(
#                 None,
#                 config,
#             )
#         else:
#             # Satisfy the tool invocation by
#             # providing instructions on the requested changes / change of mind
#             result = graph.invoke(
#                 {
#                     "messages": [
#                         ToolMessage(
#                             tool_call_id=event["messages"][-1].tool_calls[0]["id"],
#                             content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
#                         )
#                     ]
#                 },
#                 config,
#             )
#         snapshot = graph.get_state(config)

