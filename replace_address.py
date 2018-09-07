import msgpack
import zlib
import asyncpg
import aioredis
from tornado import ioloop
from bitcoinrpc_async.authproxy import AsyncAuthServiceProxy
from db import DB
from config import *
from btcpy.lib.codecs import Bech32Codec
from btcpy.setup import setup

setup('mainnet')
io_loop = ioloop.IOLoop.instance()


class Deserialize(object):
    def __init__(self, rpc_host, rpc_port, rpc_username, rpc_password, pg_host,
                 pg_port, pg_username, pg_password, pg_database,
                 redis_master_url, redis_slaves_url, logg):
        self.pg_host = pg_host
        self.pg_port = pg_port
        self.pg_username = pg_username
        self.pg_password = pg_password
        self.pg_database = pg_database
        self.redis_master_url = redis_master_url
        self.redis_slaves_url = redis_slaves_url

        self.log = logg

        self.p = lambda: AsyncAuthServiceProxy("http://%s:%s@%s:%s" % (
            rpc_username, rpc_password, rpc_host, rpc_port), timeout=10)

        self.pg = None
        self.redis_master = None
        self.redis_slaves = None
        io_loop.run_sync(self.pg_pool)
        io_loop.run_sync(self.redis_pool)

        self.db = DB(
            self.pg, (self.redis_master, self.redis_slaves), self.p(), self.log
        )

    async def pg_pool(self):
        self.pg = await asyncpg.create_pool(
            user=self.pg_username, password=self.pg_password,
            database=self.pg_database, host=self.pg_host, port=self.pg_port,
            loop=io_loop.asyncio_loop)

    async def redis_pool(self):
        self.redis_master = await aioredis.create_pool(
            self.redis_master_url, loop=io_loop.asyncio_loop)
        self.redis_slaves = await aioredis.create_pool(
            self.redis_slaves_url, loop=io_loop.asyncio_loop)

    async def get_payout(self, txid):
        comp = await self.redis_slaves.execute('GET', 't'+txid[:20])
        if not(comp is None):
            decomp = zlib.decompress(comp)
            payout = msgpack.unpackb(decomp)
            return payout
        else:
            return None

    @staticmethod
    def codec(address):
        raw_address = Bech32Codec.decode(address)
        Bech32Codec.net_to_hrp = {'mainnet': 'bcd',
                      'testnet': 'tbcd'}
        Bech32Codec.hrp_to_net = {'bcd': 'mainnet',
                      'tbcd': 'testnet'}
        bech32_address = Bech32Codec.encode(raw_address)
        Bech32Codec.net_to_hrp = {'mainnet': 'bc',
                      'testnet': 'tb'}
        Bech32Codec.hrp_to_net = {'bc': 'mainnet',
                      'tb': 'testnet'}
        return bech32_address

    async def update_utxo(self):
        count = 0
        pagesize = 100
        print("begin update utxo")
        while True:
            fetch = await self.pg.fetch("SELECT vout_id, txid, n, value, type, address FROM tx_vout WHERE height>495866 AND address LIKE 'bc1%' AND (txid, n) NOT IN "
                                        "(SELECT prev_txid, prev_n FROM tx_vin WHERE height>495866 AND address LIKE 'bc1%') LIMIT $1 OFFSET $2;", pagesize, count)
            if len(fetch) == 0:
                break
            count += len(fetch)
            for item in fetch:
                vout_id = item[0]
                txid = item[1]
                vout_n = item[2]
                vout_value = item[3]
                tx_type = item[4]
                vout_address = Deserialize.codec(item[5])

                payout = await self.get_payout(txid)
                payout[0].update({
                                str(vout_n).encode('utf-8'): [
                                    vout_id,
                                    vout_value,
                                    tx_type.encode('utf-8'),
                                    [vout_address.encode('utf-8')]
                                ]})
                # print(payout)
                self.db.set_payout_kv(txid, payout)
            print('%d data processed' % count)
        print('utxo updating finished')

    async def update_tx_vin(self):
        count = 0
        pagesize = 100
        print('begin update tx_vin')
        while True:
            fetch = await self.pg.fetch("SELECT vin_id, address FROM tx_vin WHERE height>495866 AND address LIKE 'bc1%' LIMIT $1;", pagesize)
            if len(fetch) == 0:
                break
            count += len(fetch)
            for item in fetch:
                vin_id = item[0]
                address = Deserialize.codec(item[1])
                await self.pg.execute("""UPDATE tx_vin_{} set address = $1 WHERE vin_id = $2;""".format(vin_id//5000000), address, vin_id)
                # print(vin_id, address)
            print('%d data processed' % count)
        print('tx_vin updating finished')

    async def update_tx_vout(self):
        count = 0
        pagesize = 100
        print('begin update tx_vout')
        while True:
            fetch = await self.pg.fetch("SELECT vout_id, address FROM tx_vout WHERE height>495866 AND address LIKE 'bc1%' LIMIT $1;", pagesize)
            if len(fetch) == 0:
                break
            count += len(fetch)
            for item in fetch:
                vout_id = item[0]
                address = Deserialize.codec(item[1])
                await self.pg.execute("""UPDATE tx_vout_{} set address = $1 WHERE vout_id = $2;""".format(vout_id//5000000), address, vout_id)
                # print(vout_id, address)
            print('%d data processed' % count)
        print('tx_vout updating finished')

    async def replace_address(self):
        await self.update_utxo()
        await self.update_tx_vin()
        await self.update_tx_vout()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    rpc = parser.add_argument_group("BITCOIN DIAMOND RPC")
    rpc.add_argument('--rpc-host', dest='rpc_host', type=str, default=RPC_HOST)
    rpc.add_argument('--rpc-port', dest='rpc_port', type=int, default=RPC_PORT)
    rpc.add_argument('--rpc-username', dest='rpc_username', type=str,
                     default=RPC_USERNAME)
    rpc.add_argument('--rpc-password', dest='rpc_password', type=str,
                     default=RPC_PASSWORD)
    pg = parser.add_argument_group("POSTGRES ARGUMENT")
    pg.add_argument('--pg-host', dest='pg_host', type=str, default=PG_HOST)
    pg.add_argument('--pg-port', dest='pg_port', type=int, default=PG_PORT)
    pg.add_argument('--pg-username', dest='pg_username', type=str,
                    default=PG_USERNAME)
    pg.add_argument('--pg-password', dest='pg_password', type=str,
                    default=PG_PASSWORD)
    pg.add_argument('--pg-database', dest='pg_database', type=str,
                    default=PG_DATABASE)
    parser.add_argument('--redis-master', dest='redis_master', type=str,
                        default=REDIS_MASTER)
    parser.add_argument('--redis-slaves', dest='redis_slaves', type=str,
                        default=REDIS_SLAVES)
    parser.add_argument('--log-file', dest='log_file', type=str,
                        default='./logs/sync_service.log')
    parser.add_argument('--debug', dest='debug', action='store_true')
    parser.set_defaults(debug=False)
    parser.add_argument('--start', dest='start', type=int)
    parser.add_argument('--end', dest='end', type=int, default=None)

    args = parser.parse_args()

    de = Deserialize(
        rpc_host=args.rpc_host,
        rpc_port=args.rpc_port,
        rpc_username=args.rpc_username,
        rpc_password=args.rpc_password,
        pg_host=args.pg_host,
        pg_port=args.pg_port,
        pg_username=args.pg_username,
        pg_password=args.pg_password,
        pg_database=args.pg_database,
        redis_master_url=args.redis_master,
        redis_slaves_url=args.redis_slaves,
        logg=None
    )

    io_loop.add_callback(de.replace_address)
    io_loop.start()
