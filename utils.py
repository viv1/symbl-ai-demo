import json
import pymongo
import requests

import logging
logging.getLogger("pymongo").setLevel(logging.CRITICAL)

NEBULA_EMBEDDING_URI = "https://api-nebula.symbl.ai/v1/model/embed"
NEBULA_CHAT_URI = "https://api-nebula.symbl.ai/v1/model/chat"
NEBULA_API_KEY = "" # Replace with your Nebula API Key

MONGO_DB_URI = "" # Replace with your MongoDB URI
MONGO_DB_NAME = "mydb" # Replace with your Mongo database name
MONGO_DB_COLLECTION_NAME = "mycollection" # Replace with your MongoDB collection name

SYMBL_TOKEN_URI = "https://api.symbl.ai/oauth2/token:generate"
SYMBL_APP_ID = "" # Replace with your Symbl.ai App ID
SYMBL_APP_SECRET = "" # Replace with your Symbl.ai App Secret

def get_vector_embeddings(data):
    payload = json.dumps({
        "text": data # You’ll replace this in the next step
    })
    headers = {
        'ApiKey': NEBULA_API_KEY, # Replace with your value
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", NEBULA_EMBEDDING_URI, headers=headers, data=payload)
    return response.text

def open_mondo_db_connection():
    mongoclient = pymongo.MongoClient(MONGO_DB_URI)
    db = mongoclient[MONGO_DB_NAME]
    collection = db[MONGO_DB_COLLECTION_NAME]
    return collection

def vector_index_search(tracker):
    collection = open_mondo_db_connection()
    tracker_embedding = get_vector_embeddings(tracker)
    tracker_embedding_vector = json.loads(tracker_embedding)['embedding']
    retrieved_context = collection.aggregate([
    {
        "$vectorSearch": {
            "queryVector": tracker_embedding_vector,
            "path": "embedding",
            "numCandidates": 10, #total number of embeddings in the database
            "limit": 1, #number of closest embeddings returned
            "index": "my_index"
            }
        }])
    return next(retrieved_context, None)

def generate_token():
    payload = {
        "type": "application",
        "appId": SYMBL_APP_ID,
        "appSecret": SYMBL_APP_SECRET
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(SYMBL_TOKEN_URI, json=payload, headers=headers)
    return json.loads(response.text)['accessToken']

def get_nebula_response(conversation, relevant_info):
    payload = json.dumps({
    "max_new_tokens": 1024,
    "system_prompt": f"You are a customer support agent assistant. You help the agents perform their job better by providing them relevant answers for their inputs. You are respectful, professional and you always respond politely. You also respond in clear and concise terms. The agent is currently on a call with a customer. Relevant information: {relevant_info} . Recent conversation transcript: {conversation}",
    "messages": [
        {
        "role": "human",
        "text": "Hello, I am a customer support agent. I would like to help my customers based on the given context."
        },
        {
        "role": "assistant",
        "text": "Hello. I'm here to assist you."
        },
        {
        "role": "human",
        "text": "Given the customer issue, provide me with the most helpful details that will help me resolve the customer’s issue quickly."
        }
    ]
    })

    headers = {
        'ApiKey': NEBULA_API_KEY, # Replace with your value
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", NEBULA_CHAT_URI, headers=headers, data=payload)
    print(json.loads(response.text)['messages'][-1]['text'])