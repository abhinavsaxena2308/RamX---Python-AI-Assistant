from dotenv import load_dotenv
from mem0 import MemoryClient
import logging
import json


load_dotenv()
user_name = 'RamX'
mem0 = MemoryClient()

def add_memory():
    
    messages_formatted = [
        {        "role": "user",
            "content": "i have an interview."
        },
        {
            "role": "assistant",
            "content": "which interview? shall i help you with some tips?."
        },
        {
            "role": "user",
            "content": "yes please."
        },
        {
            "role": "assistant",
            "content": "What is your favorite song by them?"
        },
    ]

    mem0.add(messages_formatted, user_id="RamX")

def get_memory_by_query():
    mem0 = MemoryClient()
    query = "What are {user_name}'s preferences?"
    results = mem0.search(query, user_id=user_name)

    memories = [
            {
                "memory": result["memory"],
                "updated_at": result["updated_at"]
            }
            for result in results
        ]
    memories_str = json.dumps(memories)
    print(f"Memories: {memories_str}")
    return memories_str


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    add_memory()