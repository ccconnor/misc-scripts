#!/usr/bin/env python3
# 创建6种交易格式输出 p2pkh\p2sh\p2wpkh\p2wsh\p2wpkh-p2sh\p2wsh-p2sh
import decimal
import hashlib
from binascii import hexlify, unhexlify
from bitcoinrpc.authproxy import AuthServiceProxy  #pip install python-bitcoinrpc
from bitcoin.transaction import serialize  # pip install python-bitcoinlib
from bitcoin.main import b58check_to_hex, hex_to_b58check
from pprint import pprint

rpc_user = 'bitcoinrpc'
rpc_password = '123456'
rpc_host = '127.0.0.1'
rpc_port = 17116

p = AuthServiceProxy("http://%s:%s@%s:%s" %
                     (rpc_user, rpc_password, rpc_host, rpc_port))
address1 = p.getnewaddress()
address2 = p.getnewaddress()
address3 = p.getnewaddress()
print('Get new address:', address1, address2, address3)
pubkey1 = p.validateaddress(address1)['pubkey']
pubkey2 = p.validateaddress(address2)['pubkey']
pubkey3 = p.validateaddress(address3)['pubkey']

multisigaddress = p.createmultisig(2, [pubkey1, pubkey2, pubkey3])['address']
redeemscript = p.createmultisig(2, [pubkey1, pubkey2, pubkey3])['redeemScript']
print('multisigaddress:', multisigaddress, '\nredeemscript:', redeemscript)
p.addmultisigaddress(2, [pubkey1, pubkey2, pubkey3])
print('addwa', p.addwitnessaddress(multisigaddress))
p.addwitnessaddress(address1)


def bytes_to_hex_str(byte_str):
    return hexlify(byte_str).decode('ascii')


def hex_str_to_bytes(hex_str):
    return unhexlify(hex_str.encode('ascii'))


def ripemd160(s):
    return hashlib.new('ripemd160', s).digest()


def sha256(s):
    return hashlib.new('sha256', s).digest()


def mk_p2wsh_script(script):
    """生成p2wsh的脚本"""
    scripthash = bytes_to_hex_str(sha256(hex_str_to_bytes(script)))
    pkscript = "0020" + scripthash
    return pkscript


def mk_p2sh_script(addr):
    print('b58check_to_hex(addr)', b58check_to_hex(addr))
    return 'a914' + b58check_to_hex(addr) + '87'


def mk_p2wpkh_script(addr):
    return '0014' + b58check_to_hex(addr)


def mk_p2pkh_script(addr):
    return '76a914' + b58check_to_hex(addr) + '88ac'


def mk_p2wpkh_in_p2sh_script(addr):
    # p2wpkh
    pubkey_20_byte_hash = '0014' + b58check_to_hex(addr)
    # p2sh
    p2sh_script_hash256 = bytes_to_hex_str(
        sha256(hex_str_to_bytes(pubkey_20_byte_hash))
    )
    p2sh_script_hash160 = bytes_to_hex_str(
        ripemd160(hex_str_to_bytes(p2sh_script_hash256))
    )
    print('p2sh-p2wpkh addr>>', hex_to_b58check(p2sh_script_hash160, 196))  # 5
    schash = 'a914' + p2sh_script_hash160 + '87'
    return schash


def mk_p2wsh_in_p2sh_script(script):
    # p2wsh
    scripthash = bytes_to_hex_str(sha256(hex_str_to_bytes(script)))
    pkscript = "0020" + scripthash
    # p2sh
    p2sh_script_hash256 = bytes_to_hex_str(sha256(hex_str_to_bytes(pkscript)))
    p2sh_script_hash160 = bytes_to_hex_str(
        ripemd160(hex_str_to_bytes(p2sh_script_hash256))
    )
    print('hex_to_b58check', hex_to_b58check(p2sh_script_hash160, 196))  # 5
    schash = 'a914' + p2sh_script_hash160 + '87'
    return schash


def select_utxo(amount, utxos=None):
    """
    :param amount: 总额(加上手续费)
    :return: [交易的输入，所有输入的总额]
    """
    ins = []
    ins_amount = 0

    listunspent = p.listunspent() if utxos is None else utxos

    # listunspent = [
    #     {
    #         'txid': '8a9a615af609de691b5f0050160c160fb8672d35cba0448f1f5c3a33fad558f9',
    #         'vout': 1, 'amount': 1, 'spendable': True
    #     }
    # ]

    for unspent in listunspent:
        if not unspent['spendable']:
            continue

        if ins_amount < amount:
            txin = {
                'script': '',
                'outpoint': {
                    'index': unspent['vout'],
                    'hash': unspent['txid']
                },
                'sequence': 4294967295
            }
            ins.append(txin)
            ins_amount += unspent['amount']
        else:
            break

    if ins_amount <= amount:
        return 0

    return [ins, ins_amount]


def create_tx(send_list, my_fee, change_addr, utxos=None):
    """
    :param send_list: [{'address':xxx, 'value':0},...]，输出
    :param my_fee: 单位BTC
    :param change_addr: 找零地址
    :return: txid
    """
    # tx
    tx = {'version': 12, 'ins': [], 'outs': [], 'locktime': 0}

    # out
    out_value_sum = 0
    for out in send_list:
        if out['type'] == 'p2wsh':
            out_script = mk_p2wsh_script(out['address'])
        elif out['type'] == 'p2sh':
            out_script = mk_p2sh_script(out['address'])
        elif out['type'] == 'p2wpkh':
            out_script = mk_p2wpkh_script(out['address'])
        elif out['type'] == 'p2pkh':
            out_script = mk_p2pkh_script(out['address'])
        elif out['type'] == 'p2sh-p2wpkh':
            out_script = mk_p2wpkh_in_p2sh_script(out['address'])
        elif out['type'] == 'p2sh-p2wsh':
            out_script = mk_p2wsh_in_p2sh_script(out['address'])
        txout = {
            'value': int(decimal.Decimal(out['value'] * 10 ** 7)),
            'script': out_script
        }
        tx['outs'].append(txout)
        out_value_sum += out['value']

    # in
    select = select_utxo(round(out_value_sum + my_fee, 7), utxos)
    # print(select)
    if select:
        ins = select[0]
        ins_value_sum = select[1]
    else:
        return '余额不足'

    tx['ins'] = ins

    # change to myself
    change_value = float(ins_value_sum) - out_value_sum - my_fee
    # print(change_value, ins_value_sum, out_value_sum, my_fee)

    if change_addr:
        txout = {
            'value': int(decimal.Decimal(change_value * 10 ** 7)),
            'script': mk_p2pkh_script(change_addr)
        }
        tx['outs'].append(txout)

    # print('tx:→', tx)

    # serialize
    raw_tx = serialize(tx)

    block_hash = '58718699a133b08aa27d8b0b71b018e6de0a2e56ab78bcc7ed916901dfb04db3'

    raw_tx = raw_tx[:8]+block_hash + raw_tx[8:]
    print('raw_tx->', raw_tx)
    # sign
    sign_raw_tx = p.signrawtransaction(raw_tx)

    # pprint(p.decoderawtransaction(sign_raw_tx['hex']))

    return p.sendrawtransaction(sign_raw_tx['hex'], True)


def spent_all(txid, pay_to):
    i = 0
    for utxo_info in pay_to:
        print('Spent %s utxo' % utxo_info['type'])
        pay = [{'address': address2, 'value': utxo_info['value']/2, 'type': 'p2pkh'}]
        utxo = [
            {
                'txid': txid,
                'vout': i, 'amount': utxo_info['value'], 'spendable': True
            }
        ]
        txhash = create_tx(pay, 0.0001, address3, utxo)
        print('txid:→', txhash)
        i += 1


if __name__ == '__main__':
    change_address = address3
    fee = 0.00001

    pay_to = [
        {'address': redeemscript, 'value': 0.1,
         'type': 'p2wsh'},
        {'address': multisigaddress, 'value': 0.1,
         'type': 'p2sh'},
        {'address': address1, 'value': 0.1,
         'type': 'p2wpkh'},
        {'address': address1, 'value': 0.1,
         'type': 'p2pkh'},
        {'address': address1, 'value': 0.1,
         'type': 'p2sh-p2wpkh'},
        {'address': redeemscript, 'value': 0.1,
         'type': 'p2sh-p2wsh'},
    ]

    txid = create_tx(pay_to, fee, change_address)
    print('txid:→', txid)

    spent_all(txid, pay_to)