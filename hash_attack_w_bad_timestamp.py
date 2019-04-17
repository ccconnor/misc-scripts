#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Python script to simulate hash attacks and timestamp manipulation.
#
# Hash Attack instructions.
# The computer running this script should be the only miner on the network.
# Change settings in this file and run script after node is running:
# python hash_attack_w_bad_timestamps.py
# CTRL-C to start and stop the attack. CTRL-C does not stop this script.
# "Stopping attack" means allowing 1-thread to mine only a fraction of the time.
# "Starting attack" means allowing continuous mining with 4 threads.
# 100x attacker can be simulated with the attack_size setting.
# kill hash_attack_w_bad_timestamps.py to stop this script.
#
# Timestamp manipulation instructions (optional).
# What you need:
# You need 1 or more other nodes & exactly 1 other 1-thread miner on 1 of them to see effect
# of > 50% timestamp attacker, provided attacker here has 4 threads. The other miner throws off
# this script's attack size calculation. Use attack_size=100 to get 4x baseline attack = 4/5 threads = 80% of
# network as the hash rate timestamp manipulator.
# If attacker here is less than 50% of network hash rate, then results are instructive but less harmful.
# The other node(s) will have the valid chain because their clock is correct.
# Get difficulties and timestamps from those nodes for analysis.
# Bad timestamp testing procedure:
# 0) Select the windows system of this node in the settings below and save script.
# 1) Turn off automatic time updates on this node.
# 2) Select 1 of the 4 recommended timestamp adjustments below, save.
# 3) Run this script in attack mode for > 10 blocks.
# 4) kill hash_attack_w_bad_timestamps.py to stop this script.
# 5) Turn on automatic time update to fix this node's system clock.
# 6) Repeat 1) to 5) above for each of the 4 recommended bad timestamp settings.
# 7) Analyze difficulties and timestamps from the other nodes to see the results.

import signal
import time
import subprocess
import win32api
from bitcoinrpc.authproxy import AuthServiceProxy

mainnet = {
    'rpc_user': 'bitcoinrpc',
    'rpc_password': '123456',
    'rpc_host': '127.0.0.1',
    'rpc_port': 7116
}

testnet = {
    'rpc_user': 'bitcoinrpc',
    'rpc_password': '123456',
    'rpc_host': '127.0.0.1',
    'rpc_port': 17116
}

bitcoin_rpc = None
attack_miner = None
dedicated_miner = None
attack_miner_log = 'attack_miner.log'
dedicated_miner_log = 'dedicated_miner.log'
stratum_server = '127.0.0.1:3333'

interrupted = 0
target_solve_time = 600
attack_size = 10
attacker_threads = 4
dedicated_threads = 1

use_timestamp_manipulation = 0
bad_timestamp_size = 0.5 * target_solve_time

last_height = 0


def set_windows_time(seconds):
    tm = time.gmtime(seconds)
    win32api.SetSystemTime(tm.tm_year, tm.tm_mon, tm.tm_wday, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec, 0)


def get_dedicated_miner_off_time():
    global target_solve_time
    global attack_size
    global attacker_threads
    global dedicated_threads
    return int((1 - attacker_threads / dedicated_threads / (attack_size + 1)) * target_solve_time)


def set_net_type(network):
    global bitcoin_rpc
    if network == 'mainnet':
        net = mainnet
    elif network == 'testnet':
        net = testnet
    else:
        return
    bitcoin_rpc = AuthServiceProxy("http://%s:%s@%s:%s"
                                   % (net['rpc_user'], net['rpc_password'], net['rpc_host'], net['rpc_port']))


def sleep(secs):
    try:
        time.sleep(secs)
    except IOError:
        pass


def sigint_handler(sig, frame):
    global interrupted
    interrupted = 1


def start_miner(thread_num, output):
    global stratum_server
    print('start %s threads miner' % thread_num)
    return subprocess.Popen('ccminer -a bcd -o stratum+tcp://%s '
                            '-u 15DG8HmCHU2Lzc7VpEEhY15iRMCBcje5DY.1234 -p x -t %s' % (stratum_server, thread_num),
                            stdout=output,
                            stderr=output,
                            creationflags=subprocess.DETACHED_PROCESS)


def stop_miner(miner):
    try:
        miner.terminate()
    except Exception as e:
        print('stop miner failed.', e)


def get_last_height():
    try:
        return bitcoin_rpc.getblockcount()
    except Exception as e:
        print('getblockcount failed.', e)
        global last_height
        return last_height


def main():
    global interrupted
    global dedicated_miner
    global attack_miner
    global dedicated_miner_log
    global attack_miner_log
    global last_height

    signal.signal(signal.SIGINT, sigint_handler)

    set_net_type('testnet')

    dedicated_miner_output = open(dedicated_miner_log, 'w')
    attack_miner_output = open(attack_miner_log, 'w')

    dedicated_miner_off_time = get_dedicated_miner_off_time()

    dedicated_miner = start_miner(dedicated_threads, dedicated_miner_output)
    last_height = get_last_height()

    while True:
        sleep(1)
        if interrupted == 1:
            interrupted = 0
            print('starting attack')
            attack_miner = start_miner(attacker_threads, attack_miner_output)

            while interrupted == 0:
                sleep(1)
                height = get_last_height()
                if height != last_height:
                    last_height = height
                    print('attacker found', height)
                    if use_timestamp_manipulation == 1:
                        set_windows_time(int(time.time()) + bad_timestamp_size)
            interrupted = 0
            stop_miner(attack_miner)
            print('attack stopped')

        height = get_last_height()
        if height != last_height:
            last_height = height
            print('dedicated miner found', height)
            stop_miner(dedicated_miner)
            print('miner sleeping for %s seconds' % dedicated_miner_off_time)
            sleep(dedicated_miner_off_time)
            print('starting dedicated miner')
            start_miner(dedicated_threads, dedicated_miner_output)


if __name__ == '__main__':
    main()
