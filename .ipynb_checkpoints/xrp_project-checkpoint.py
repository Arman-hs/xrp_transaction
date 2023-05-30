import sqlite3

import xrpl
from xrpl.clients import JsonRpcClient


database_name = 'xrp_project.db'
table_name = 'transactions'

def create_table(con, table_name):
    command = '''create table if not exists transactions (tx_hash text,
                outcome text,
                amount real,
                destination text,
                destination_tag integer,
                source text)
                '''
    con.execute(command)
    

def insert_transaction_to_db(con, transaction, table_name):
    command = f'''
        insert into {table_name} 
        select "{transaction.tx_hash}", "{transaction.outcome}", {transaction.amount},
        "{transaction.destination}", {transaction.destination_tag}, "{transaction.source}"
        where not exists(select * from {table_name} where tx_hash = "{transaction.tx_hash}")
        '''
    con.execute(command)


class Transaction():
    def __init__(self, tx_hash, outcome=None, amount=None,
        destination=None, destination_tag=None, source=None) -> None:
        self.tx_hash = tx_hash
        self.outcome = outcome
        self.amount = amount
        self.destination = destination
        self.destination_tag = destination_tag
        self.source = source
        
    
    def extract_info_from_json(self, json_obj):
        # transaction status
        self.outcome = json_obj['meta']['TransactionResult']

        # transaction amount
        self.amount = json_obj['meta']['delivered_amount']
        self.amount = float(self.amount)/1000000

        # destination
        self.destination = json_obj['Destination']
        self.destination_tag = json_obj['DestinationTag']

        # source
        self.source = json_obj['Account']


def retrieve_transaction_result(tx_hash):
    JSON_RPC_URL = "https://s2.ripple.com:51234/"
    client = JsonRpcClient(JSON_RPC_URL)
    transaction_response = xrpl.transaction.get_transaction_from_hash(tx_hash=tx_hash, client=client)
    result = transaction_response.result
    return result
    
    
def main():
    # get transaction info
    tx_hash = input('Enter tx_hash of your transaction:\n> ')
    transaction_json = retrieve_transaction_result(tx_hash)
    transaction = Transaction(tx_hash)
    transaction.extract_info_from_json(transaction_json)
    print("transaction info extracted")
    # create database connection
    con = sqlite3.connect(database_name)
    create_table(con, table_name)
    # insert transaction to the table
    insert_transaction_to_db(con, transaction, table_name)
    print('done')
    
    
    
    
    

if __name__ == '__main__':
    main()