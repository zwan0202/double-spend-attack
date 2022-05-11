class ChainManager:
    def __init__(self, chain_len):
        self.chain_len = chain_len

    def is_updated(self, len):
        if len > self.chain_len:
            self.chain_len = len
            return True
        return False
