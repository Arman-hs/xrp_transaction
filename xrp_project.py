import sqlite3

import xrpl
from xrpl import transaction
from xrpl.clients import JsonRpcClient


database_name = 'xrp_project.db'
table_name = 'transactions'
amount_thres = 2

def create_table(con, table_name):
    command = f'''create table if not exists {table_name} (tx_hash text,
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
        
    
    # check amount
    def check_validity(self):
        return self.amount >= amount_thres


def retrieve_transaction_result(tx_hash):
    JSON_RPC_URL = "https://s2.ripple.com:51234/"
    client = JsonRpcClient(JSON_RPC_URL)
    transaction_response = xrpl.transaction.get_transaction_from_hash(tx_hash=tx_hash, client=client)
    result = transaction_response.result
    return result


def show_num_transaction(con):
    command = f'select count(*) from {table_name}'
    cur = con.execute(command)
    result, = cur.fetchone()
    return result
    
    
def main():
    while True:
        # get transaction info
        tx_hash = input('Enter tx_hash of your transaction:\n> ')
        if tx_hash == 'exit':
            break
        transaction_json = retrieve_transaction_result(tx_hash)
        transaction = Transaction(tx_hash)
        transaction.extract_info_from_json(transaction_json)
        print("transaction info extracted")
        # create database connection
        con = sqlite3.connect(database_name)
        create_table(con, table_name)
        # insert transaction to the table
        insert_transaction_to_db(con, transaction, table_name)
        is_user_authorized = transaction.check_validity()
        if is_user_authorized:
            transactions_num = show_num_transaction(con)
            print(f'Total of {transactions_num} people have paid at least {amount_thres} XRP',
                  f'to see how many people have paid {amount_thres} XRP')
        else:
            print(f"Your transaction amount is not equal or greater than {amount_thres}")
        con.commit()
        print('done')
        con.close()
        # TODO:
        # 1- Check Destination address and tag --> must be our account
        # 2- Handle error input
        # 3- Show the results only once for each tx_hash
        # 4- Deploy on the web using flask
        # 5- Support other currencies on the XRP blockchain network
    
    
    
    
    

if __name__ == '__main__':
    main()