#!/usr/bin/python
import boto3
import boto3_alternator
import time
import concurrent.futures
import random
from tqdm import tqdm
import logging
from threading import Lock
from botocore.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Balancing
#alternator_url = boto3_alternator.setup1(
#    # A list of known Alternator nodes. One of them must be responsive.
#    ['192.168.100.101'],
#    # Alternator scheme (http or https) and port
#    'http', 8000,
#    # A "fake" domain name which, if used by the application, will be
#    # resolved to one of the Scylla nodes.
#    'myalternator.app.com'
#)

# Configure botocore with increased max_pool_connections
my_config = Config(
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    },
    connect_timeout=5,
    read_timeout=10,
    max_pool_connections=1000
)

# Without Load Balancing
alternator_url = 'http://192.168.100.101:8000'

# Initialize the DynamoDB resource
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
    table_name = 'test_table'
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

def generate_new_data():
    """
    Generates new data for the update operation.
    Modify this function based on your actual data generation logic.
    """
    # Example implementation returning a string consistent with 'data' attribute
    return f"Updated data {random.randint(1, 1000000)}"

def put_item(item_id):
    table = dynamodb.Table('test_table')
    try:
        table.put_item(
            Item={
                'id': item_id,
                'data': f'Data for item {item_id}'
            }
        )
    except Exception as e:
        logger.error(f"Error putting item {item_id}: {e}")

def get_item(item_id):
    table = dynamodb.Table('test_table')
    try:
        response = table.get_item(
            Key={
                'id': item_id
            }
        )
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {e}")
        return None

def update_item(item_id, new_data):
    table = dynamodb.Table('test_table')
    try:
        table.update_item(
            Key={
                'id': item_id
            },
            UpdateExpression='SET data = :val1',
            ExpressionAttributeValues={
                ':val1': new_data
            }
        )
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}")

def delete_item(item_id):
    table = dynamodb.Table('test_table')
    try:
        table.delete_item(
            Key={
                'id': item_id
            }
        )
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")

def stress_test(num_iterations, progress_bar, lock):
    """
    Performs stress testing by executing put, get, update, and delete operations.

    :param num_iterations: Number of iterations to perform.
    :param progress_bar: Shared tqdm progress bar instance.
    :param lock: Lock object to synchronize progress bar updates.
    """
    for _ in range(num_iterations):
        item_id_put = random.randint(1, 1000000)
        item_id_get = random.randint(1, 1000000)
        item_id_update = random.randint(1, 1000000)
        item_id_delete = random.randint(1, 1000000)
        new_data = generate_new_data()

        # Perform Put Operation
        put_item(item_id_put)
        with lock:
            progress_bar.update(1)

        # Perform Get Operation
        get_item(item_id_get)
        with lock:
            progress_bar.update(1)

        # Perform Update Operation
        update_item(item_id_update, new_data)
        with lock:
            progress_bar.update(1)

        # Perform Delete Operation
        delete_item(item_id_delete)
        with lock:
            progress_bar.update(1)

def run_stress_tests_concurrently(total_iterations=100000, concurrency=100):
    """
    Runs stress tests concurrently using ThreadPoolExecutor.

    :param total_iterations: Total number of stress test iterations.
    :param concurrency: Number of concurrent threads.
    """
    start_time = time.time()

    # Create the table once
    create_table()

    # Calculate iterations per thread
    iterations_per_thread = total_iterations // concurrency
    remaining_iterations = total_iterations % concurrency

    # Initialize the progress bar
    total_operations = total_iterations * 4  # 4 operations per iteration
    pbar = tqdm(total=total_operations, desc="Stress Testing")
    lock = Lock()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(concurrency):
            # Distribute the remaining iterations among the first few threads
            if i < remaining_iterations:
                iters = iterations_per_thread + 1
            else:
                iters = iterations_per_thread
            #print(f"Starting thread {i}")
            futures.append(executor.submit(stress_test, iters, pbar, lock))

        # Optionally, handle futures as they complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"An error occurred in a stress test thread: {e}")

    pbar.close()
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"Finished {total_iterations} iterations ({total_operations} operations) in {total_time:.2f} seconds.")

if __name__ == "__main__":
    print("Starting!!!")
    run_stress_tests_concurrently(total_iterations=100000, concurrency=1)
    print("Ended!!!")
