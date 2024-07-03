import json
from utils import get_vector_embeddings, open_mondo_db_connection


def parse_text(text):
    data = []
    current_key = None
    current_value = []

    for line in text.splitlines():
        line = line.strip()

        # Start of a new section
        if line.startswith("----"):
            if current_key and current_value:
                data.append({
                    "key": current_key,
                    "value": "\n".join(current_value)
                })
                current_value = []

            # Extract key from the same line as ----
            current_key = line[4:].strip() 
        
        # Handle lines within a section (not empty and not a key line)
        elif current_key and line and not line.startswith("----"):
            current_value.append(line)

    # Capture the last section if it exists
    if current_key and current_value:
        data.append({
            "key": current_key,
            "value": "\n".join(current_value)
        })

    return data

def populate_knowledge_data():
    parsed_data = []
    with open('knowledge_data.txt') as f:
        parsed_data = parse_text(f.read())

    for data in parsed_data:
        key_embedding = get_vector_embeddings(data['key'])
        document = {
            'data': data['value'],
            'embedding': json.loads(key_embedding)['embedding']
        }
        collection = open_mondo_db_connection()
        collection.insert_one(document)

def main():
    populate_knowledge_data()

if __name__ == "__main__":
    main()