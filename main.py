import api_key
from helper import _print_event
from datetime import datetime
import uuid
import os
import time
from httpx import HTTPStatusError
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from tools import (
    fetch_product_by_title,
    fetch_product_by_category,
    fetch_product_by_brand,
    initialize_fetch,
    fetch_all_categories,
    fetch_recommendations,
    add_to_cart,
    remove_from_cart,
    view_checkout_info,
    get_delivery_estimate,
    get_payment_options,
    
)
from graph import ShoppingGraph
from db_init import init_database

def main():
    # Инициализация базы данных
    init_database()
    
    # Инициализация модели Mistral
    llm = init_chat_model("mistral-large-latest", model_provider="mistralai")

    # Шаблон для ассистента
    primary_assistant_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a helpful shopping assistant and stylist dedicated to providing accurate and friendly responses. "
        "Use the available tools to answer product queries, recommend items, manage the shopping cart, and provide checkout information, delivery times, and payment options. "
        "Additionally, you can provide style recommendations for different situations (e.g., business meeting, party, casual day), suggest complete outfits, and recommend matching accessories. "
        "Always ensure that all product, availability, and price information is sourced from the database. "
        "When handling product queries, ensure all parameters that are not explicitly provided by the user are set to `None` instead of an empty string. "
        "Use the appropriate tools to retrieve delivery times, payment methods, and style recommendations. "
        "Avoid making guesses or assumptions if required database information is unavailable. "
        "If a tool returns an empty response, kindly ask the user to rephrase their question or provide additional details. "
        "Ensure that you only communicate capabilities you possess, and if any tool function returns an error, relay the error message to the user in a helpful manner."
        "\n\nCurrent user:\n<User>\n{user_info}\n</User>"
        "\nCurrent time: {time}.",
    ),
    ("placeholder", "{messages}"),
    ]).partial(time=datetime.now())

    # Привязка инструментов
    tools_no_confirmation = [
        fetch_product_by_title,
        fetch_product_by_category,
        fetch_product_by_brand,
        initialize_fetch,
        fetch_all_categories,
        fetch_recommendations,
        view_checkout_info,
        get_delivery_estimate,
        get_payment_options,
    ]
    tools_need_confirmation = [add_to_cart, remove_from_cart]
    confirmation_tool_names = {t.name for t in tools_need_confirmation}

    assistant_runnable = primary_assistant_prompt | llm.bind_tools(
        tools_no_confirmation + tools_need_confirmation
    )

    # Создание ShoppingGraph
    shopping_graph = ShoppingGraph(assistant_runnable, tools_no_confirmation, tools_need_confirmation)

    # Уникальный ID сессии
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "user_id": thread_id,
            "thread_id": thread_id,
        }
    }

    print("Please wait for initialization")
    
    # Инициализация с обработкой rate limit
    initial_query = "Please welcome me, and show me some available products and category."
    max_attempts = 5
    attempt = 0
    while attempt < max_attempts:
        try:
            initial_events = shopping_graph.stream_responses({"messages": ("user", initial_query)}, config)
            break
        except HTTPStatusError as err:
            if err.response.status_code == 429:  # Rate limit
                retry_after = int(err.response.headers.get("Retry-After", 10))
                print(f"Rate limit exceeded during initialization. Waiting {retry_after} seconds before retrying...")
                time.sleep(retry_after)
            else:
                print(f"An HTTP error occurred: {err}")
                break
            attempt += 1

    if initial_events is None:
        print("Failed to fetch initial products after multiple attempts.")
        return

    for event in initial_events:
        final_result = event
    final_result["messages"][-1].pretty_print()

    print("\nType your question below (or type 'exit' to end):\n")

    # Основной цикл с улучшенной обработкой rate limit
    while True:
        question = input("\nYou: ")
        if question.lower() == 'exit':
            print("Ending session. Thank you for using the shopping assistant!")
            break

        attempt = 0
        while attempt < max_attempts:
            try:
                events = shopping_graph.stream_responses({"messages": ("user", question)}, config)
                _printed = set()
                for event in events:
                    _print_event(event, _printed)
                break
            except HTTPStatusError as err:
                if err.response.status_code == 429:  # Rate limit
                    retry_after = int(err.response.headers.get("Retry-After", 10))
                    print(f"Rate limit exceeded. Waiting {retry_after} seconds before retrying...")
                    time.sleep(retry_after)
                    attempt += 1
                else:
                    print(f"An HTTP error occurred: {err}")
                    break
        if attempt == max_attempts:
            print("Failed to process your request after multiple attempts.")

        # Обработка подтверждений
        snapshot = shopping_graph.get_state(config)
        while snapshot.next:
            try:
                user_input = input(
                    "\nAre you sure about that? Type 'y' to continue;"
                    " otherwise, explain your requested changed.\n"
                )
            except:
                user_input = "y"
            if user_input.strip() == "y":
                result = shopping_graph.invoke(None, config)
                print(result['messages'][-1].content)
            else:
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

if __name__ == "__main__":
    main()