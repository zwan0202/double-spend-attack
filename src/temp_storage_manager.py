import sys
import os
from pathlib import Path

myDir = os.getcwd()
sys.path.append(myDir)
path = Path(myDir)
absolute_path = str(path.parent.absolute())
sys.path.append(absolute_path)

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from src.blockchain.blockchain import Blockchain
from src.blockchain.block import Block
from src.constant import HOST


app = Flask(__name__)
CORS(app)
ports = set()
attack_ports = set()
fork_chain = None
dsa_success = False


@app.route('/ports/all')
def all_ports():
    response = {'ports': list(ports)}
    return jsonify(response)


@app.route('/ports/all/other/')
def all_other_ports():
    current_port = request.args.get('current_port')
    other_ports = ports.difference({current_port})
    response = {'ports': list(other_ports)}
    return jsonify(response)


@app.route('/ports/add/', methods=['POST'])
def add_port():
    port = request.args.get('port')
    try:
        register_port(port)
    except ValueError:
        pass

    response = {'port': port}

    return jsonify(response)


@app.route('/chain/fork', methods=['POST'])
def fork_blockchain():
    global fork_chain

    response = {}
    if not fork_chain:
        fork_chain = Blockchain.from_json(request.get_json())

        response['or_chain'] = fork_chain.to_json()

        fork_chain.fork()
        response['forked'] = True
    else:
        response['forked'] = False

    response['fork_chain'] = fork_chain.to_json()

    return jsonify(response)


@app.route('/chain/fork')
def get_fork_chain():
    if fork_chain:
        response = {
            'fork_chain': fork_chain.to_json(),
            'len': len(fork_chain.chain)
        }
        return jsonify(response)

    return jsonify({'fork_chain': None, 'len': 0})


@app.route('/chain/fork/clear')
def clear_fork_chain():
    global fork_chain
    if fork_chain:
        fork_chain = None

    return jsonify({'fork_chain': None})


@app.route('/chain/fork/add/block', methods=['POST'])
def fork_chain_add_block():
    response = {}
    if fork_chain:
        potential_block_json = request.get_json()

        if fork_chain.add_block(Block.from_json(potential_block_json)):
            response['added'] = True
        else:
            response['added'] = False
        response['len'] = len(fork_chain.chain)
        response['fork_chain'] = fork_chain.to_json()

    return jsonify(response)


@app.route('/chain/fork/broadcast')
def broadcast_chain():
    bc_response = {
        'success_ports': [],
        'fail_ports': []
    }
    if fork_chain:
        for port in ports:
            url = f'http://{HOST}:{port}/chain/resolve'
            response = requests.post(url, json=fork_chain.to_json())
            if response.status_code == 200:
                if response.json()['success']:
                    bc_response['success_ports'].append(port)
                else:
                    bc_response['fail_ports'].append(port)

    return jsonify(bc_response)


@app.route('/dsa/success')
def get_dsa_success():
    return jsonify({'dsa_success': dsa_success})


@app.route('/dsa/success/set/true', methods=['POST'])
def set_dsa_success_true():
    global dsa_success
    dsa_success = True

    return jsonify({'dsa_success': dsa_success})


@app.route('/dsa/success/set/false', methods=['POST'])
def set_dsa_success_false():
    global dsa_success
    dsa_success = False

    return jsonify({'dsa_success': dsa_success})


def register_port(port):
    # if is_port_in_use(port):
    #     ports.add(port)
    #     print(f'add port {port}')
    # else:
    #     print(f'port {port} not in use')
    ports.add(port)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8001, debug=True)
