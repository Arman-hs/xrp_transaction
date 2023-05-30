from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from loguru import logger

import xrpl
from xrpl.clients import JsonRpcClient

# Parameters
amount_thres = 2
dest_address = 'rEb8TK3gBgk5auZkwc6sHnwrGVJH8DuaLh' 
dest_tag = 103544552

# Errors
amount_not_satisfied = f'AMOUNT IS NOT EQUAL OR GREATER THAN {amount_thres} XRP'
dest_not_satisfied = f'Destination address is not equal to {dest_address}'
dest_tag_not_satisfied = f'Destination Tag is not equal to {dest_tag}'

app = Flask(__name__) # __name__ == '__main__'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///xrp_project.db'
db = SQLAlchemy(app)


def retrieve_transaction_result(tx_hash):
    JSON_RPC_URL = "https://s2.ripple.com:51234/"
    client = JsonRpcClient(JSON_RPC_URL)
    transaction_response = xrpl.transaction.get_transaction_from_hash(tx_hash=tx_hash, client=client)
    result = transaction_response.result
    return result


class CryptoTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tx_hash = db.Column(db.String(200), unique=True, nullable=False)
    outcome = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    destination_tag = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, tx_hash=None, outcome=None, amount=None,
        destination=None, destination_tag=None, source=None,
        date_created=None, **kwargs) -> None:
        super(CryptoTransaction, self).__init__(**kwargs)
        self.tx_hash = tx_hash
        self.outcome = outcome
        self.amount = amount
        self.destination = destination
        self.destination_tag = destination_tag
        self.source = source
        self.date_created = date_created


    def extract_info_from_json(self, json_obj):
        # transaction status
        self.outcome = json_obj['meta']['TransactionResult']

        # transaction amount
        self.amount = json_obj['meta']['delivered_amount']
        self.amount = float(self.amount)/1000000

        # destination
        try:
            self.destination = json_obj['Destination']
            self.destination_tag = json_obj['DestinationTag']
        except:
            self.destination = 'ERROR'
            self.destination_tag = 0


        # source
        self.source = json_obj['Account']

    
    # check whether the transaction satisfies our requirements
    def is_valid(self):
        if self.amount < amount_thres:
            return False, amount_not_satisfied
        elif self.destination != dest_address:
            return False, dest_not_satisfied
        elif self.destination_tag != dest_tag:
            return False, dest_tag_not_satisfied
        return True, 'Success'



    
    def __str__(self) -> str:
        return 'success'


@app.route('/success')
def success():

    transaction_count = CryptoTransaction.query.count()
    return str(transaction_count)



@app.route('/', methods=['POST', 'GET'])
def index():
    logger.debug('Entered the index')
    if request.method == 'POST':
        tx_hash = request.form['tx_hash']
        transaction_json = retrieve_transaction_result(tx_hash)
        crypto_transaction = CryptoTransaction(tx_hash)
        crypto_transaction.extract_info_from_json(transaction_json)

        # check transaction's validity
        valid, status = crypto_transaction.is_valid()

        # TODO do not change valid to true
        valid = True

        if not valid:
            return(status)
        else:
            exists = bool(CryptoTransaction.query.filter_by(tx_hash=crypto_transaction.tx_hash).count())
            logger.debug(f'Entered the first else with exists = {exists}')
            if not exists:
                db.session.add(crypto_transaction)
                db.session.commit()
            else:
                crypto_transaction = CryptoTransaction.query.filter_by(tx_hash=crypto_transaction.tx_hash).first()
            total_transactions_num = CryptoTransaction.query.filter(
                    CryptoTransaction.date_created < crypto_transaction.date_created
                ).count()
            return render_template('result.html', total_num=total_transactions_num)

    else:
        transactions = CryptoTransaction.query.all()
        total_transactions_num = CryptoTransaction.query.count()
        return render_template('index.html', transactions=transactions, total_num=total_transactions_num)



if __name__ == '__main__':
    app.run(debug=True)


# TODO: Show the number of transactions before the entered user transaction