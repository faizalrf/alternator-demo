import logging
import re
import time
import random
from alternator_lb import AlternatorLB, Config as ALBConfig
import botocore.httpsession
import urllib3.connection

# -----------------------------------
# Custom Logging Filter
# -----------------------------------
class AlternatorNodeLogFilter(logging.Filter):
    def filter(self, record):
        return bool(re.search(r'http://\d+\.\d+\.\d+\.\d+:8000', record.getMessage()))

# -----------------------------------
# Base Logger Setup
# -----------------------------------
logging.basicConfig(
    level=logging.INFO  # Set higher default to reduce spam
)
logger = logging.getLogger("AlternatorNodeLogger")
logger.propagate = False
logger.setLevel(logging.DEBUG)

# Add a dedicated handler just for filtered Alternator node output
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.addFilter(AlternatorNodeLogFilter())
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# -----------------------------------
# Patch urllib3 to log only node connection events
# -----------------------------------
_original_send = botocore.httpsession.URLLib3Session.send

def patched_send(self, request):
    logger.debug(f"HTTP Request → {request.url}")
    return _original_send(self, request)

botocore.httpsession.URLLib3Session.send = patched_send

# -----------------------------------
# Alternator LB Setup
# -----------------------------------
lb = AlternatorLB(ALBConfig(
    schema="http",
    nodes=['10.1.0.3'],  # Add more if available
    port=8000,
    datacenter="DC1",
    update_interval=5,
    max_pool_connections=100,
))

dynamodb = lb.new_botocore_dynamodb_client()
table_name = 'test_table'


# -----------------------------------
# Create Table
# -----------------------------------
def create_table():
    try:
        dynamodb.describe_table(TableName=table_name)
        logger.info(f"Table '{table_name}' exists. Deleting...")
        dynamodb.delete_table(TableName=table_name)

        # Wait until deleted
        while True:
            try:
                dynamodb.describe_table(TableName=table_name)
                time.sleep(1)
            except dynamodb.exceptions.ResourceNotFoundException:
                break
        logger.info(f"Table '{table_name}' deleted.")
    except dynamodb.exceptions.ResourceNotFoundException:
        logger.info(f"Table '{table_name}' does not exist. Creating...")

    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'N'}],
        ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10}
    )
    logger.info(f"Table '{table_name}' created.")


# -----------------------------------
# Write Items
# -----------------------------------
def write_items(n):
    logger.info(f"Writing {n} items to table '{table_name}'")
    start = time.time()
    for i in range(n):
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'id': {'N': str(i)},
                'payload': {'S': f'data_{i}'}
            }
        )
    end = time.time()
    logger.info(f"Wrote {n} items in {end - start:.2f} seconds")


def read_items(n):
    logger.info(f"Reading {n} items from table '{table_name}'")
    start = time.time()
    for _ in range(n):
        rand_id = random.randint(0, n - 1)
        dynamodb.get_item(
            TableName=table_name,
            Key={'id': {'N': str(rand_id)}}
        )
    end = time.time()
    logger.info(f"Read {n} items in {end - start:.2f} seconds")

# -----------------------------------
# Main
# -----------------------------------
if __name__ == "__main__":
    #create_table()
    write_items(100) 
    read_items(100)