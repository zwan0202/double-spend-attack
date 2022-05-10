class IPAdrr:
    def __init__(self):
        import socket

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            self.ip = s.getsockname()[0]
        except Exception:
            self.ip = '127.0.0.1'
        finally:
            s.close()

SECONDS = 1

DSA_DURATION = 60 * SECONDS
DSA_TIMEOUT = 10 * SECONDS

DIFFICULTY = 16

# replace with host ip if connect from guest device
HOST = IPAdrr().ip
TEMP_STORAGE_PORT = '8001'

# adjusted difficulty
MINE_RATE = 4 * SECONDS

MINING_REWARD = 1
MINING_REWARD_INPUT = {'address': '*--mining-reward--*'}
