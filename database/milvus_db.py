from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
from sentence_transformers import SentenceTransformer

# Configuration
MILVUS_HOST = 'localhost'
MILVUS_PORT = '19530'
OPENAI_API_KEY = 'provide openAI key here'
MODEL_NAME = 'all-MiniLM-L6-v2'
COLLECTION_NAME = 'testing_products'

# Connect to Milvus
conn_milvus = connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
# Get the existing collection
collection_milvus = Collection(name=COLLECTION_NAME)

# Initialize the sentence transformer model
model = SentenceTransformer(MODEL_NAME)


def create_schema(collection_name):
    # COLLECTION_NAME = 'testing_products'
    # Define the schema for Milvus collection
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="brand", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=384)
    ]
    schema = CollectionSchema(fields, "Deals collection schema for testing database")
    collection = Collection(COLLECTION_NAME, schema)
    return collection


def text_to_vector(description):
    return model.encode(description).tolist()


def search_similar(description):
    query_vector = text_to_vector(description)
    search_params = {"metric_type": "L2", "offset": 0, "ignore_growing": False, "params": {"nprobe": 10}}
    results = collection_milvus.search([query_vector], "vector", search_params, limit=10, output_fields=["id", "brand", "category", "description"])
    return results