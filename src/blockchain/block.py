import time
import requests
import src.util as util
from src.blockchain.chain_manager import ChainManager
from src.constant import DIFFICULTY, MINE_RATE, HOST, UPDATE_DURATION

GENESIS_DATA = {
    'timestamp': 0,
    'block_idx': 0,
    'last_hash': 'genesis_last_hash',
    'block_hash': 'genesis_hash',
    'transactions': [],
    'nonce': 'genesis_nonce',
    'public_key': 'genesis_public_key'
}

class Block:

    def __init__(self, timestamp, block_idx, last_hash, block_hash, transactions, nonce, public_key):
        self.block_hash = block_hash
        self.block_idx = block_idx
        self.last_hash = last_hash
        self.nonce = nonce
        self.public_key = public_key
        self.timestamp = timestamp
        self.transactions = transactions

    def __eq__(self, other):
        return self.block_hash == other.block_hash

    def __repr__(self):
        return (
            '{'
            f'index: {self.block_idx}, '
            f'hash: {self.block_hash}, '
            f'last_hash: {self.last_hash}, '
            f'nonce: {self.nonce}, '
            f'timestamp: {self.timestamp}, '
            f'transactions: {self.transactions}'
            '}'
        )

    @staticmethod
    def genesis():
        return Block(**GENESIS_DATA)

    def to_json(self):
        return self.__dict__

    @staticmethod
    def from_json(block_json):
        return Block(**block_json)

    @staticmethod
    def mine_block(last_block, transactions, public_key, is_fork, port):
        timestamp = time.time_ns()
        block_idx = last_block.block_idx + 1
        nonce = 0
        last_hash = last_block.block_hash
        block_hash = util.crypto_hash(timestamp, block_idx, nonce, last_hash, transactions, public_key)

        chain_manger = ChainManager(Block.get_chain_len(port))
        s = time.time()
        e = time.time()

        while Block.not_meet_difficulty(block_hash):
            if not is_fork:
                d = e - s
                if d > UPDATE_DURATION:
                    if chain_manger.is_updated(Block.get_chain_len(port)):
                        # print('Chain changed ')
                        return None
                    s = time.time()
            nonce += 1
            block_hash = util.crypto_hash(timestamp, block_idx, nonce, last_hash, transactions, public_key)
            e = time.time()

        return Block(timestamp, block_idx, last_hash, block_hash, transactions, nonce, public_key)

    @staticmethod
    def not_meet_difficulty(block_hash):
        return util.hex_to_binary(block_hash)[0:DIFFICULTY] != '0' * DIFFICULTY

    @staticmethod
    def get_chain_len(port):
        request_url = f'http://{HOST}:{port}/length'
        response = requests.get(request_url)
        if response.status_code == 200:
            len = response.json()['len']
            return len
        else:
            print(f'Error in port {port}')

        return 0

    @staticmethod
    def adjust_difficulty(last_block, new_timestamp):
        if (new_timestamp - last_block.timestamp) < MINE_RATE:
            return last_block.difficulty + 1

        if (last_block.difficulty - 1) > 0:
            return last_block.difficulty - 1

        return 1

    @staticmethod
    def is_valid_block(last_block, block):
        if block.last_hash != last_block.block_hash:
            raise Exception('The block last_hash not match')

        if Block.not_meet_difficulty(block.block_hash):
            raise Exception('The proof of work requirement was not met')
        block_hash = util.crypto_hash(
            block.timestamp,
            block.block_idx,
            block.nonce,
            block.last_hash,
            block.transactions,
            block.public_key
        )

        return True
