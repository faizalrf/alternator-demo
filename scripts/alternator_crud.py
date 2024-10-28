import boto3
import time
import concurrent.futures
import random
import boto3_alternator
from tqdm import tqdm
from botocore.config import Config

#Load Balancing
#alternator_url = boto3_alternator.setup2(
#    # A list of known Alternator nodes. One of them must be responsive.
#    ['192.168.100.101'],
#    # Alternator scheme (http or https) and port
#    'http', 8000,
#    # A "fake" domain name which, if used by the application, will be
#    # resolved to one of the Scylla nodes.
#    'myalternator.app.com')

# Without Load Balancing
alternator_url = 'http://192.168.100.101:8000'

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

print(dynamodb.meta.client.describe_endpoints()['Endpoints'][0]['Address'])

def create_table():
    start_time = time.time()
    table_name = 'test_table'
    table = dynamodb.Table(table_name)
    
    # Check if the table exists and then DROP it
    try:
        table.load()
        print(f"Table {table_name} exists. Deleting table...")
        # Delete the table
        table.delete()
        # Wait until the table is deleted
        table.wait_until_not_exists()
        print(f"Table {table_name} deleted.")
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        print(f"Table {table_name} does not exist. Proceeding to create it.")
    
    # Create the new table
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'id',
                'AttributeType': 'N'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )

    table.wait_until_exists()
    end_time = time.time()
    print(f"Table {table_name} created successfully in {end_time - start_time:.2f} seconds.")

def write_items():
    start_time = time.time()
    create_table()
    table = dynamodb.Table('test_table')
    with table.batch_writer() as batch:
        for i in range(1, 100_001):
            batch.put_item(
                Item={
                    'id': i,
                    'data': f'Data for item {i}'
                }
            )
            if i % 1000 == 0:
                print(f'{i} items written.')

    end_time = time.time()
    print(f"Finished writing {i} items in {end_time - start_time:.2f} seconds.")

def write_items_single():
    start_time = time.time()
    create_table()
    table = dynamodb.Table('test_table')
    for i in range(1, 100_001):
        table.put_item(
            Item={
                'id': i,
                'data': f'Data for item {i}'
            }
        )
        if i % 1000 == 0:
            current_time = time.time()
            elapsed = current_time - start_time
            print(f'{i} items written in {elapsed:.2f} seconds.')
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Finished writing {i} items in {total_time:.2f} seconds.")

def write_items_concurrent():
    start_time = time.time()
    create_table()
    table_name = 'test_table'
    total_items = 1_000_000
    batch_size = 200

    def insert_items(start, end):
        table = dynamodb.Table(table_name)
        for i in range(start, end):
            table.put_item(
                Item={
                    'id': i,
                    'data': f'Data for item {i}'
                }
            )

    ranges = [(i, min(i + batch_size, total_items + 1)) for i in range(1, total_items + 1, batch_size)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(insert_items, start, end): (start, end) for start, end in ranges}

        # Optional: Progress monitoring
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            start_range, end_range = futures[future]
            completed += (end_range - start_range)
            if completed % 1000 == 0:
                current_time = time.time()
                elapsed = current_time - start_time
                print(f'{completed} items written in {elapsed:.2f} seconds.')
            try:
                future.result()
            except Exception as e:
                print(f'An error occurred: {e}')

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Finished writing {total_items} items in {total_time:.2f} seconds.")

def get_item(item_id):
    table = dynamodb.Table('test_table')
    try:
        response = table.get_item(
            Key={
                'id': item_id
            }
        )
    except Exception as e:
        print(f"Error fetching item: {e}")
        return

    item = response.get('Item')

def create_item(item_id, data):
    start_time = time.time()

    table = dynamodb.Table('test_table')
    try:
        table.put_item(
            Item={
                'id': item_id,
                'data': data
            }
        )
        print(f"Item {item_id} created.")
    except Exception as e:
        print(f"Error creating item: {e}")

    end_time = time.time()
    print(f"Table created successfully in {end_time - start_time:.2f} seconds.\n")

def read_item(item_id):
    get_item(item_id)

def stress_test():
    total_iterations = 100000
    total_operations = total_iterations * 4

    with tqdm(total=total_operations, desc="Stress Testing") as pbar:
        for i in range(1, total_iterations + 1):
            item_id_put = random.randint(1, 1000000)
            item_id_get = random.randint(1, 1000000)
            item_id_update = random.randint(1, 1000000)
            item_id_delete = random.randint(1, 1000000)
            new_data = generate_new_data()

            # Perform Put Operation
            put_item(item_id_put)
            pbar.update(1)

            # Perform Get Operation
            get_item(item_id_get)
            pbar.update(1)

            # Perform Update Operation
            update_item(item_id_update, new_data)
            pbar.update(1)

            # Perform Delete Operation
            delete_item(item_id_delete)
            pbar.update(1)

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
        print(f"Error updating item: {e}")

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
        print(f"Error updating item: {e}")

def delete_item(item_id):
    table = dynamodb.Table('test_table')
    try:
        table.delete_item(
            Key={
                'id': item_id
            }
        )
    except Exception as e:
        print(f"Error deleting item: {e}")

def generate_new_data():
    return {
        'score': {'N': str(random.randint(1, 100))}
    }
    
# Execute the functions
#create_table()
#write_items()
#write_items_single()
write_items_concurrent()
#stress_test()
#get_item(500)
#create_item(1000001, 'Data for new item')
#read_item(1000001)
#update_item(1000001, 'Updated data for new item')
#read_item(1000001)
#delete_item(1000001)
#read_item(1000001)