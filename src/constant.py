class IPAdrr:
    def __init__(self):
        import socket

        hostname = socket.gethostname()
        self.ip = socket.gethostbyname(hostname)

SECONDS = 1

DSA_DURATION = 60 * SECONDS
DSA_TIMEOUT = 10 * SECONDS

DIFFICULTY = 16

# replace with host ip
HOST = ''
TEMP_STORAGE_PORT = '8001'

# adjusted difficulty
MINE_RATE = 4 * SECONDS

MINING_REWARD = 1
MINING_REWARD_INPUT = {'address': '*--mining-reward--*'}
