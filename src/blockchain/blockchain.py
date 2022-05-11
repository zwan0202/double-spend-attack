from src.blockchain.block import Block
from src.wallet.transaction import Transaction

class Blockchain:

    def __init__(self):
        self.chain = [Block.genesis()]

    def __repr__(self):
        return f'Blockchain: {self.chain}'

    def to_json(self):
        return list(map(lambda block: block.to_json(), self.chain))

    @staticmethod
    def from_json(chain_json):
        blockchain = Blockchain()
        blockchain.chain = list(
            map(lambda block_json: Block.from_json(block_json), chain_json)
        )

        return blockchain

    def add_block(self, potential_block):
        last_block = self.chain[-1]
        if (potential_block.last_hash == last_block.block_hash) and (Block.is_valid_block(last_block, potential_block)):
            self.chain.append(potential_block)
            return True
        return False

    def replace_chain(self, chain):
        r_chain = chain.chain
        if len(r_chain) > len(self.chain):
            try:
                Blockchain.is_valid_chain(chain)
            except Exception:
                raise Exception('The incoming chain is invalid')

            self.chain = r_chain

            return True
        return False

    @staticmethod
    def is_valid_chain(chain):
        c_chain = chain.chain
        for i in range(1, len(c_chain)):
            block = c_chain[i]
            last_block = c_chain[i - 1]
            Block.is_valid_block(last_block, block)
            for transaction_json in block.transactions:
                transaction = Transaction.from_json(transaction_json)
                Transaction.is_valid_transaction(transaction)
        return True

    def fork(self):
        if len(self.chain) > 1:
            self.chain = self.chain[:-1]
