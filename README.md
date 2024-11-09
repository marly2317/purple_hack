# Shopping Assistant with LangGraph

## Overview
This project is a Shopping Assistant developed using LangChain, LangGraph, and a local language model (LLM). The assistant can handle various shopping-related queries, manage a shopping cart, and provide information on product availability, recommendations, delivery estimates, and payment options.

The assistant is built using tools for interacting with a local SQLite database and handle sensitive operations (like adding/removing items from the cart) by requiring user confirmation.

## Prerequisites
Ollama with LLaMA 3.2: You need to run Ollama with the LLaMA 3.2 model locally to handle conversational capabilities of the assistant. It is recommended to use at least a 3B parameter model for optimal performance.

Python 3.11 or higher

SQLite




## Installation
#### Clone the repository:

```
git clone https://github.com/yourusername/shopping-assistant-langgraph.git
cd shopping-assistant-langgraph
```



#### Set up a virtual environment:

```
python3 -m venv venv
source venv/bin/activate  # For Max or Linux systems
venv\Scripts\activate  # For Windows
```



#### Install dependencies:

```
pip install -r requirements.txt
```



#### Set up the database:

Please run `populate_database.py` to get SQLite database file named shopping_assistant.sqlite with a products table and a cart table



#### Start Ollama:

Run Ollama with LLaMA 3.2 locally, ensuring it is properly configured to handle at least a 3B model size for performance.



#### Run the Shopping Assistant:

```
python main.py
```



#### Interactive Mode:

The assistant will prompt you to type your shopping-related queries. Common operations include:

1. Searching for products by title, category, brand.
2. Adding/removing items from the cart with confirmation.
3. Viewing cart details, checking out, and retrieving payment options.

The assistant will provide feedback and responses based on the operations it performs.

Here is some example：

User: "Please show me some available products in the beauty category."

Assistant: "Here are some available beauty products:

1. Essence Mascara Lash Princess - $9.99
2. Red Lipstick - $12.99
..."

User: "Add Essence Mascara Lash Princess to my cart."

Assistant: "Are you sure you want to add this product to your cart? Type 'y' to confirm or provide additional instructions."

User: "y"

Assistant: "The item has been added to your cart."
