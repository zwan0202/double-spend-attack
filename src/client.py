import sys
import os
from pathlib import Path

myDir = os.getcwd()
sys.path.append(myDir)
path = Path(myDir)
absolute_path = str(path.parent.absolute())
sys.path.append(absolute_path)

import time
import requests
import logging
from random import choice
from threading import Thread, Event
from flask import Flask
from flask_cors import CORS
from src.blockchain.blockchain import Blockchain
from src.blockchain.block import Block
from src.blockchain.chain_manager import ChainManager
from src.wallet.wallet import Wallet
from src.wallet.transaction import (Transaction, TransactionPool)
from src.constant import HOST, TEMP_STORAGE_PORT, MINING_REWARD_INPUT, DSA_DURATION, DSA_TIMEOUT


app = Flask(__name__)
CORS(app)
log = logging.getLogger('werkzeug')
log.disabled = True
port = ''
role = ''
dsa_success = 0
dsa_count = 0
chainManager = ChainManager(0)
transaction_pool = TransactionPool()
wallet = Wallet()
exit_event = Event()
threads = {}
res = []


def main_menu():
    while True:
        print(f'\n======= Port: {port} =======\n'
              f'======== {role} ========\n'
              f'1. Connect to Port\n'
              f'2. Mine\n'
              f'3. Broadcast Blockchain\n'
              f'4. Start Auto Mine\n'
              f'5. Stop Auto Mine\n'
              f'6. Double Spend Attack\n'
              f'7. New Transaction\n'
              f'8. All Transactions\n'
              f'9. Blockchain Info\n'
              f'0. Exit')

        execute_menu(input(' >> '))


def execute_menu(m_choice):
    if m_choice == '':
        return
    else:
        try:
            menu_actions[m_choice]()
        except KeyError:
            print('Invalid choice')
        return


def quit_app():
    quit()


def connect_port():
    print('======= Connect port ========\n'
          'Available ports: ')
    print(all_ports())

    global port
    port = input('Enter port number >> ')

    return


def all_ports():
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/ports/all'
    response = requests.get(request_url)
    if response.status_code == 200:
        return response.json()['ports']
    else:
        print('Cannot connect to ports manager')
        return []


def mine(tran_pool=None):
    if not tran_pool:
        tran_pool = transaction_pool

    added = False
    while not added:
        blockchain_json, len = get_blockchain()
        blockchain = Blockchain.from_json(blockchain_json)
        reward_transaction, exist = tran_pool.find_transaction(MINING_REWARD_INPUT['address'])

        if not exist:
            reward_transaction = Transaction.reward_transaction(wallet.address)
            tran_pool.add_transaction(reward_transaction)

        transactions = tran_pool.all_transactions()

        potential_block = Block.mine_block(blockchain.chain[-1], transactions, wallet.public_key, False, port)

        if potential_block:
            request_url = f'http://{HOST}:{port}/chain/add/block'
            potential_block_json = potential_block.to_json()
            response = requests.post(request_url, json=potential_block_json)

            if response.status_code == 200:
                added = response.json()['added']

    print(Block.from_json(potential_block_json))
    tran_pool.clear_transactions()

    return


def broadcast_blockchain():
    request_url = f'http://{HOST}:{port}/chain/broadcast'
    response = requests.get(request_url)
    if response.status_code == 200:
        success_ports = response.json()['success_ports']
        fail_ports = response.json()['fail_ports']
        # print(f'success_ports: {success_ports} ===== fail_ports: {fail_ports}')

    return


def start_auto_mine():
    exit_event.clear()
    thread = Thread(target=auto_mine_thread, daemon=True)
    threads['auto_mine'] = thread
    thread.start()


def auto_mine_thread():
    print('===== Auto Mine Started ======')
    while not exit_event.is_set():
        mine()
        broadcast_blockchain()
    return


def stop_auto_mine():
    exit_event.set()
    thread = threads['auto_mine']
    thread.join()
    print('====== Auto Mine Stopped ======')


def get_blockchain():
    request_url = f'http://{HOST}:{port}/chain'
    response = requests.get(request_url)
    if response.status_code == 200:
        chain = response.json()['chain']
        len = response.json()['len']

        return chain, len
    else:
        print(f'Error in port {port}')

    return None


def get_fork_blockchain():
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/chain/fork'
    response = requests.get(request_url)
    if response.status_code == 200:
        chain = response.json()['fork_chain']

        return chain

    return None


def is_timeout(start_time, curr_time, timeout):
    duration = curr_time - start_time
    if duration > timeout:
        print('====== DSA Timeout =======')
        return True
    else:
        return False


def double_spend_attack():
    set_main_attacker('true')

    attack_start_time = time.time()
    timeout = is_timeout(attack_start_time, time.time(), DSA_DURATION)

    global dsa_count, dsa_success
    dsa_count = 0
    dsa_success = 0

    while not timeout:
        if not get_fork_blockchain():
            dsa_transaction()
            fork_blockchain()

        following_dsa = dsa_auto_mine(attack_start_time)

        if not following_dsa:
            dsa_broadcast_fork_chain()
            clear_fork_chain()
            set_dsa_success('false')

        dsa_count += 1
        timeout = is_timeout(attack_start_time, time.time(), DSA_DURATION)

    if get_main_attacker():
        dsa_success_rate = round(dsa_success / dsa_count * 100, 2)
        res.append('=========================================\n'
                   '=               DSA  Result             =\n'
                   '=========================================\n'
                   f'Total DSA Performed: {dsa_count}\n'
                   f'Success: {dsa_success}\n'
                   f'Success rate: {dsa_success_rate} %')

        with open("../result.txt", "w") as f:
            for r in res:
                f.write(r)

    return


def fork_blockchain():
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/chain/fork'
    chain_json, len = get_blockchain()

    response = requests.post(request_url, json=chain_json)
    if response.status_code == 200:
        forked = response.json()['forked']
        print(f'===== Fork block chain =====\n'
              f'Forked {forked}')

        return forked


def dsa_auto_mine(attack_start_time):
    global dsa_count, dsa_success

    print('\n====== Double Spend Attack Start ======')
    fork_chain_len = 0
    fork_chain_json = ''
    public_chain_len = 0
    public_chain_json = ''
    success = False
    following_dsa = False

    dsa_start_time = time.time()
    dsa_timeout = is_timeout(dsa_start_time, time.time(), DSA_TIMEOUT)
    attack_timeout = is_timeout(attack_start_time, time.time(), DSA_DURATION)

    while not success:
        if attack_timeout or dsa_timeout:
            print(f'dsa_auto_mine timeout : attack_timeout {attack_timeout} : dsa_timeout {dsa_timeout}')
            break
        if fork_chain_len <= public_chain_len:
            fork_chain_json, fork_chain_len = fork_chain_add_block(attack_start_time, dsa_start_time)
            public_chain_json, public_chain_len = get_blockchain()
            success = get_dsa_success()
            if success:
                following_dsa = True
                return following_dsa
        else:
            success = set_dsa_success('true')

        attack_timeout = is_timeout(attack_start_time, time.time(), DSA_DURATION)
        dsa_timeout = is_timeout(dsa_start_time, time.time(), DSA_TIMEOUT)

    if not attack_timeout and not dsa_timeout:
        dsa_success += 1
        r = '====== Double Spend Attack Complete ======\n'
    else:
        r = '====== Double Spend Attack Timeout ======\n'

    r += f'Current try: {dsa_count + 1}\nFork chain len: {fork_chain_len}\n{Blockchain.from_json(fork_chain_json)}\nPublic chain len: {public_chain_len}\n{Blockchain.from_json(public_chain_json)}\n\n'
    res.append(r)

    return following_dsa


def get_main_attacker():
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/main/attacker'
    response = requests.get(request_url)
    if response.status_code == 200:
        return response.json()['main_attacker']
    return


def set_main_attacker(is_main):
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/main/attacker/set/{is_main}'
    response = requests.post(request_url)
    if response.status_code == 200:
        return response.json()['main_attacker']
    return


def get_dsa_success():
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/dsa/success'
    response = requests.get(request_url)
    if response.status_code == 200:
        return response.json()['dsa_success']
    return


def set_dsa_success(success):
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/dsa/success/set/{success}'
    response = requests.post(request_url)
    if response.status_code == 200:
        return response.json()['dsa_success']
    return


def dsa_broadcast_fork_chain():
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/chain/fork/broadcast'
    response = requests.get(request_url)
    if response.status_code == 200:
        success_ports = response.json()['success_ports']
        fail_ports = response.json()['fail_ports']
        # print(f'success_ports: {success_ports} ===== fail_ports: {fail_ports}')

    return


def fork_chain_add_block(attack_start_time, dsa_start_time):
    added = False
    len = 0
    fork_chain_json = ''
    dsa_transaction_pool = TransactionPool()

    dsa_timeout = is_timeout(dsa_start_time, time.time(), DSA_TIMEOUT)
    attack_timeout = is_timeout(attack_start_time, time.time(), DSA_DURATION)

    while not added:
        if attack_timeout or dsa_timeout:
            print('fork_chain_add_block timeout : attack_timeout {attack_timeout} : dsa_timeout {dsa_timeout}')
            break
        get_fork_chain_json = get_fork_blockchain()
        if not get_fork_chain_json:
            break
        fork_chain = Blockchain.from_json(get_fork_chain_json)
        reward_transaction, exist = dsa_transaction_pool.find_transaction(MINING_REWARD_INPUT['address'])

        if not exist:
            reward_transaction = Transaction.reward_transaction(wallet.address)
            dsa_transaction_pool.add_transaction(reward_transaction)

        transactions = dsa_transaction_pool.all_transactions()

        potential_block = Block.mine_block(fork_chain.chain[-1], transactions, wallet.public_key, True, TEMP_STORAGE_PORT)

        request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/chain/fork/add/block'
        potential_block_json = potential_block.to_json()
        response = requests.post(request_url, json=potential_block_json)

        if response.status_code == 200:
            added = response.json()['added']
            len = response.json()['len']
            fork_chain_json = response.json()['fork_chain']
        else:
            break

        dsa_timeout = is_timeout(dsa_start_time, time.time(), DSA_TIMEOUT)
        attack_timeout = is_timeout(attack_start_time, time.time(), DSA_DURATION)

    print(Block.from_json(potential_block_json))

    return fork_chain_json, len


def dsa_transaction():
    print('\n===== DSA Transaction Start =======')
    recipient = 'DOUBLE SPEND ATTACK'
    amount = 'AMOUNT'

    transaction = Transaction(
        wallet.address,
        wallet.public_key,
        wallet.generate_signature(Transaction.create_output(recipient, amount)),
        recipient,
        amount
    )

    tran_pool = TransactionPool()
    tran_pool.add_transaction(transaction)

    mine(tran_pool)
    broadcast_blockchain()

    print('====== DSA Transaction Complete =====')

    return


def clear_fork_chain():
    request_url = f'http://{HOST}:{TEMP_STORAGE_PORT}/chain/fork/clear'
    requests.get(request_url)
    return


def new_transaction():
    print('======= New Transaction =========')
    recipient = input('Recipient: ')
    amount = input('Amount: ')

    transaction = Transaction(
        wallet.address,
        wallet.public_key,
        wallet.generate_signature(Transaction.create_output(recipient, amount)),
        recipient,
        amount
    )

    transaction_pool.add_transaction(transaction)
    print(transaction.to_json())

    return


def all_transactions():
    print('========== All Transactions ===========')
    print(transaction_pool.all_transactions())
    return


def config_role():
    print('========== Config Role =========\n'
          '1. Normal\n'
          '2. Attack')
    execute_role(input(' >> '))


def execute_role(choose):
    global port
    ports = all_ports()
    port = choice(ports)

    try:
        role_option[choose]()
    except KeyError:
        print('Invalid choice')
    return


def normal_role():
    global role
    role = 'Normal'
    # start_auto_mine()


def attack_role():
    global role
    role = f'Attack'
    # double_spend_attack()


def observer_role():
    global role
    role = f'Observer'


def blockchain_info():
    chain_json, len = get_blockchain()
    print(f'====== Get Blockchain =======\n'
          f'Len: {len}\n'
          f'{chain_json}')


menu_actions = {
    'main_menu': main_menu,
    '0': quit_app,
    '1': connect_port,
    '2': mine,
    '3': broadcast_blockchain,
    '4': start_auto_mine,
    '5': stop_auto_mine,
    '6': double_spend_attack,
    '7': new_transaction,
    '8': all_transactions,
    '9': blockchain_info
}

role_option = {
    '1': normal_role,
    '2': attack_role,
    '3': observer_role
}


if __name__ == '__main__':
    config_role()
    main_menu()
