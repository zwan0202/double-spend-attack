import time
import uuid
from src.wallet.wallet import Wallet
from src.constant import MINING_REWARD, MINING_REWARD_INPUT

class Transaction:

    def __init__(self,
                 sender_address=None,
                 sender_pub_key=None,
                 signature=None,
                 recipient=None,
                 amount=None,
                 transaction_id=None,
                 output=None,
                 input=None
                 ):
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.output = output or self.create_output(recipient, amount)
        self.input = input or self.create_input(sender_address, sender_pub_key, signature)

    def to_json(self):
        return self.__dict__

    @staticmethod
    def from_json(transaction_json):
        return Transaction(**transaction_json)

    @staticmethod
    def create_output(recipient, amount):
        return {recipient: amount}

    @staticmethod
    def create_input(sender_address, sender_pub_key, signature):
        return {
            'timestamp': time.time_ns(),
            'address': sender_address,
            'public_key': sender_pub_key,
            'signature': signature
        }

    @staticmethod
    def is_valid_transaction(transaction):
        if transaction.input == MINING_REWARD_INPUT:
            if list(transaction.output.values()) != [MINING_REWARD]:
                raise Exception('Invalid mining reward')
            return

        if not Wallet.verify_signature(
                public_key=transaction.input['public_key'],
                data=transaction.output,
                signature=transaction.input['signature']
        ):
            raise Exception('Invalid signature')

    @staticmethod
    def reward_transaction(wallet_address):
        output = Transaction.create_output(wallet_address, MINING_REWARD)
        return Transaction(input=MINING_REWARD_INPUT, output=output)

class TransactionPool:

    def __init__(self):
        self.transaction_map = {}

    def add_transaction(self, transaction):
        self.transaction_map[transaction.transaction_id] = transaction

    def find_transaction(self, address):
        for transaction in self.transaction_map.values():
            if transaction.input['address'] == address:
                return transaction, True
        return None, False

    def all_transactions(self):
        return list(map(lambda transaction: transaction.to_json(), self.transaction_map.values()))

    def clear_transactions(self):
        self.transaction_map.clear()
