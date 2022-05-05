import time
import double_spend_attack.util as util
from double_spend_attack.constant import DIFFICULTY, MINE_RATE

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

    @staticmethod
    def genesis():
        return Block(**GENESIS_DATA)

    def to_json(self):
        return self.__dict__

    @staticmethod
    def from_json(block_json):
        return Block(**block_json)

    @staticmethod
    def mine_block(last_block, transactions, public_key):
        timestamp = time.time_ns()
        block_idx = last_block.block_idx + 1
        nonce = 0
        last_hash = last_block.block_hash
        block_hash = util.crypto_hash(timestamp, block_idx, nonce, last_hash, transactions, public_key)

        while Block.not_meet_difficulty(block_hash):
            nonce += 1
            block_hash = util.crypto_hash(timestamp, block_idx, nonce, last_hash, transactions, public_key)

        return Block(timestamp, block_idx, last_hash, block_hash, transactions, nonce, public_key)

    @staticmethod
    def not_meet_difficulty(block_hash):
        return util.hex_to_binary(block_hash)[0:DIFFICULTY] != '0' * DIFFICULTY

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
