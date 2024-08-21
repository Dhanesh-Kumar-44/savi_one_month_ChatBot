from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Milvus
conn_milvus = connections.connect(host=os.getenv("MILVUS_HOST"), port=os.getenv("MILVUS_PORT"))
# Get the existing collection
collection_milvus = Collection(name=os.getenv("COLLECTION_NAME"))

# Initialize the sentence transformer model
model = SentenceTransformer(os.getenv("MODEL_NAME"))

def text_to_vector(description):
    return model.encode(description).tolist()


def search_similar(description):
    query_vector = text_to_vector(description)
    search_params = {"metric_type": "L2", "offset": 0, "ignore_growing": False, "params": {"nprobe": 10}}
    results = collection_milvus.search([query_vector], "vector", search_params, limit=10, output_fields=["id", "brand", "category", "description"])
    return results