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
    recommend_capsule_wardrobe,
    recommend_style,
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
            """Вы AI-стилист с четкими правилами работы. Основные задачи:

1. При запросах со словами "гардероб", "комплект", "набор" ИСПОЛЬЗОВАТЬ ИНСТРУМЕНТ recommend_capsule_wardrobe
2. Для деловых встреч использовать категорию "Business Clothing"
3. Обязательные параметры:
   - gender: male/female (определять из контекста)
   - max_price: бюджет (указывать явно)
   
Пример вызова:
{{"tool": "recommend_capsule_wardrobe", "args": {{"situation": "деловая встреча", "gender": "male", "max_price": 100}}}}

Текущее время: {time}"""
        ),
        ("placeholder", "{messages}"),
    ]).partial(time=datetime.now())

    # Привязка инструментов
    tools_no_confirmation = [
        recommend_capsule_wardrobe,
        recommend_style,
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