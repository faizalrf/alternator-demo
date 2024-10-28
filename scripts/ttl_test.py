import boto3
import boto3_alternator
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError
import logging
import random
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Load Balancing
alternator_url = boto3_alternator.setup2(
    # A list of known Alternator nodes. One of them must be responsive.
    ['192.168.100.101'],
    # Alternator scheme (http or https) and port
    'http', 8000,
    # A "fake" domain name which, if used by the application, will be
    # resolved to one of the Scylla nodes.
    'myalternator.app.com')

my_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard',
    },
    connect_timeout=5,
    read_timeout=10,
    max_pool_connections=1000
)

# Configure boto3 client
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    aws_access_key_id='MyDummyKeyId',
    aws_secret_access_key='MyDummySecretAccessKey',
    endpoint_url=alternator_url,
    config=my_config
)

def create_table():
    """
    Creates the DynamoDB table if it doesn't already exist.
    """
    table_name = 'ttl_test'
    existing_tables = dynamodb.meta.client.list_tables()['TableNames']
    if table_name not in existing_tables:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'N'  # Number type
                }
            ],
            ProvisionedThroughput={  # These values are placeholders and not enforced by Scylla
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        # Wait until the table exists
        table.wait_until_exists()
        logger.info(f"Table '{table_name}' created successfully.")
    else:
        logger.info(f"Table '{table_name}' already exists.")

def enable_ttl(table_name, ttl_attribute):
    client = dynamodb.meta.client

    try:
        response = client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': ttl_attribute
            }
        )
        logger.info(f"TTL update response for table '{table_name}': {response}")

    except Exception as e:
        logger.error(f"Unexpected error while updating TTL for table '{table_name}': {e}")

def disable_ttl(table_name, ttl_attribute):
    client = dynamodb.meta.client

    try:
        response = client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': False,
                'AttributeName': ttl_attribute
            }
        )
        logger.info(f"TTL update response for table '{table_name}': {response}")

    except Exception as e:
        logger.error(f"Unexpected error while updating TTL for table '{table_name}': {e}")

def check_ttl_status(table_name):
    client = dynamodb.meta.client

    try:
        response = client.describe_time_to_live(TableName=table_name)
        ttl_spec = response.get('TimeToLiveDescription', {})
        status = ttl_spec.get('TimeToLiveStatus')
        attribute = ttl_spec.get('AttributeName')

        logger.info(f"TTL Status for table '{table_name}': {status}")
        logger.info(f"TTL Attribute for table '{table_name}': {attribute}")

    except Exception as e:
        logger.error(f"Unexpected error while describing TTL for table '{table_name}': {e}")

def add_item_with_ttl(table, item_id, data, ttl_seconds):
    current_time = int(time.time())
    expiration_time = current_time + random.randint(1, ttl_seconds)  # Unix epoch time

    try:
        table.put_item(
            Item={
                'id': item_id,
                'data': f"{data}-{item_id}",
                'ExpiresAt': expiration_time
            }
        )
        logger.info(f"Added item with ID {item_id} set to expire at {expiration_time}.")
    except Exception as e:
        logger.error(f"Error adding item with ID {item_id}: {e}")

def get_item(item_id, retries=3):
    table = dynamodb.Table('ttl_test')
    attempt = 0
    try:
        response = table.get_item(
            Key={
                'id': item_id
            }
        )
        item = response.get('Item')
        if item:
            print(f"Retrieved item: {item}")
        else:
            print(f"Item with ID {item_id} not found.")
        return item
    except Exception as e:
        logger.error(f"Unexpected error getting item {item_id}: {e}")

    logger.error(f"Failed to get item {item_id} after {retries} attempts.")
    return None

def main():
    table_name = 'ttl_test'
    ttl_attribute = 'ExpiresAt'  # Ensure this attribute exists and is set correctly on your items

    # Step 1: Create the table if it doesn't exist
    create_table()

    # Step 2: Enable TTL on the table
    enable_ttl(table_name, ttl_attribute)

    # Step 3: Check the TTL status
    check_ttl_status(table_name)

    # Step 4: Add an item with TTL
    table = dynamodb.Table(table_name)
    data = "Sample Data"
    ttl_seconds = 10  # Item will expire in 10 seconds
    
    # Write
    for item_id in range(10):
        add_item_with_ttl(table, item_id, data, ttl_seconds)
    
    # Fetch with TTL Enabled
    while True:
        all_none = True
        for item_id in range(10):
            item = get_item(item_id)
            if item is not None:
                all_none = False
        print("")
        time.sleep(3)
        if all_none:
            break
        
    #print("Disable TTL on the table `ttl_test`")
    # Step 2: Enable TTL on the table
    
    #disable_ttl(table_name, ttl_attribute)
    #print("Add item to the table with TTL time")

    #for item_id in range(10):
    #    add_item_with_ttl(table, item_id, data, ttl_seconds)

    ## Fetch After TTL Disabled
    #while True:
    #    all_none = True
    #    for item_id in range(10):
    #        item = get_item(item_id)
    #    print("")
    #    time.sleep(3)

if __name__ == "__main__":
    main()