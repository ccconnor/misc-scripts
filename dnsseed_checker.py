import tornado.ioloop
import tornado.web
import socket
import json
from datetime import datetime

dnsseeds = ['seed1.dns.btcd.io',
            'seed2.dns.btcd.io',
            'seed3.dns.btcd.io',
            'seed4.dns.btcd.io',
            'seed5.dns.btcd.io',
            'seed6.dns.btcd.io']

settings = {'debug': True}


def lookup_host():
    ip_list = set()
    for seed in dnsseeds:
        try:
            result = socket.getaddrinfo(seed, None, 0, socket.SOCK_STREAM)
            if len(result) == 0:
                print(datetime.today(), seed, 'no good peers')
                return []
            for item in result:
                ip_list.add(item[4][0])
        except Exception as e:
            print(datetime.today(), seed, e)
            return []
    return list(ip_list)


class DefaultHandler(tornado.web.RequestHandler):
    def get(self):
        raise tornado.web.HTTPError(400)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        ip_list = lookup_host()
        if len(ip_list) != 0:
            print(datetime.today(), ip_list)
            self.write(json.dumps(ip_list))
        else:
            raise tornado.web.HTTPError(500)


def make_app():
    return tornado.web.Application([
        (r"/dnsseed", MainHandler),
        (r".*", DefaultHandler),
    ], **settings)


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
