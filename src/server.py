import sys
import os
from pathlib import Path

myDir = os.getcwd()
sys.path.append(myDir)
path = Path(myDir)
absolute_path = str(path.parent.absolute())
sys.path.append(absolute_path)

import requests
from random import randint
from flask import Flask, jsonify, request
from flask_cors import CORS
from src.blockchain.blockchain import Blockchain
from src.blockchain.block import Block
from src.util import is_port_in_use
from src.constant import HOST

app = Flask(__name__)
CORS(app)
blockchain = Blockchain()


@app.route('/')
def index():
    return ''


@app.route('/chain')
def chain():
    response = {
        'chain': blockchain.to_json(),
        'len': len(blockchain.chain)
    }
    return jsonify(response)


@app.route('/length')
def chain_length():
    return jsonify(len(blockchain.chain))


@app.route('/chain/add/block', methods=['POST'])
def add_block():
    response = {}

    potential_block_json = request.get_json()

    if blockchain.add_block(Block.from_json(potential_block_json)):
        block = blockchain.chain[-1]
        response['block'] = block.to_json()
        response['added'] = True
    else:
        response['block'] = 'Invalid block'
        response['added'] = False

    return jsonify(response)


@app.route('/chain/broadcast')
def broadcast_chain():
    ports = all_other_ports()

    bc_response = {
        'success_ports': [],
        'fail_ports': []
    }

    for port in ports:
        url = f'http://{HOST}:{port}/chain/resolve'
        response = requests.post(url, json=blockchain.to_json())
        if response.status_code == 200:
            if response.json()['success']:
                bc_response['success_ports'].append(port)
            else:
                bc_response['fail_ports'].append(port)

    return jsonify(bc_response)


@app.route('/chain/resolve', methods=['POST'])
def resolve_chain():
    rs_chain_json = request.get_json()
    rs_chain = Blockchain.from_json(rs_chain_json)

    response = {
        'message': f'Current len: {len(blockchain.chain)}\nIncoming len: {len(rs_chain.chain)}'
    }

    try:
        if blockchain.replace_chain(rs_chain):
            response['success'] = True
        else:
            response['success'] = False
    except Exception:
        raise ValueError('Invalid chain')

    return jsonify(response)


def all_other_ports():
    url = f'http://{HOST}:8001/ports/all/other/?current_port={server_port}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['ports']
    else:
        print('Cannot connect to ports manager')
        return ''


if __name__ == '__main__':
    server_port = randint(5001, 5999)

    while is_port_in_use(server_port):
        server_port = randint(5001, 5999)

    print('======= register node ========')
    request_url = f'http://{HOST}:8001/ports/add/?port={str(server_port)}'
    requests.post(request_url)

    app.run(host=HOST, port=server_port, debug=True, use_reloader=False)
