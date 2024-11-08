from helper import _print_event
from datetime import datetime
import uuid
from langchain_core.messages import ToolMessage
# Set up the language model for the assistant
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from tools import (
    fetch_product_info,
    fetch_some_products,
    fetch_all_categories,
    fetch_recommendations,
    add_to_cart,
    remove_from_cart,
    view_checkout_info,
    get_delivery_estimate,
    get_payment_options,
)
from graph import ShoppingGraph


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
            "Always ensure that any product, availability, price information comes from the database, "
            "also make sure delivery time and pyment method use the related tools to get the information, "
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
    fetch_some_products,
    fetch_all_categories,
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

# try:
#     # Generate the image and save it to a file
#     image_data = graph.get_graph(xray=True).draw_mermaid_png()
#     with open("graph_output.png", "wb") as f:
#         f.write(image_data)
#     print("Image saved as graph_output.png")
# except Exception as e:
#     print("An error occurred:", e)
#     pass

# Instantiate the ShoppingGraph
shopping_graph = ShoppingGraph(assistant_runnable, tools_no_confirmation, tools_need_confirmation)

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
        # Use the thread_id as the user_id for the shopping assistant for now
        "user_id": thread_id,
        "thread_id": thread_id,
    }
}

_printed = set()

print("Please wait for initilization")

# Initial query to display some products when the assistant starts
initial_query = "Please welcome me, and show me some available products and category."

# Make an initial call to the assistant for the predefined query
initial_events = shopping_graph.stream_responses({"messages": ("user", initial_query)}, config)

# Print only the assistant's responses from the initial query
for event in initial_events:
    final_result = event

final_result["messages"][-1].pretty_print()

print("\nType your question below (or type 'exit' to end):")

# Start an interactive loop for user questions
while True:
    # Prompt the user to type a question
    question = input("You: ")
    
    # Break the loop if the user types 'exit'
    if question.lower() == 'exit':
        print("Ending session. Thank you for using the shopping assistant!")
        break

    # Stream responses
    events = shopping_graph.stream_responses({"messages": ("user", question)}, config)
    
    # Print each event response from the assistant
    for event in events:
        _print_event(event, _printed)
    
    # Get the graph state after processing the question
    snapshot = shopping_graph.get_state(config)
    
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
            result = shopping_graph.invoke(
                None,
                config,
            )
            print("Successfully!")
        else:
            # Satisfy the tool invocation by
            # providing instructions on the requested changes / change of mind
            result = shopping_graph.invoke(
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
        snapshot = shopping_graph.get_state(config)
