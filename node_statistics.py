import csv
import os
import requests
from bitcoinrpc.authproxy import AuthServiceProxy

rpc_user = '123'
rpc_password = '123456'
rpc_host = '127.0.0.1'
rpc_port = 7116

p = AuthServiceProxy("http://%s:%s@%s:%s" %
                     (rpc_user, rpc_password, rpc_host, rpc_port))


def get_peer_info():
    address = []
    file_name = 'peers.csv'
    if not os.path.exists(file_name):
        with open(file_name, 'a', newline='') as csv_file:
            file_header = ['address', 'version']
            writer = csv.writer(csv_file)
            writer.writerow(file_header)

    with open(file_name, 'r') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            address.append(row[0])

    with open(file_name, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        info = p.getpeerinfo()
        for item in info:
            if item['addr'] not in address:
                writer.writerow([item['addr'], item['subver'][1:-1]])
            else:
                print(item['addr'], 'already exists')


def get_ip_location(ip):
    location = ''
    url = 'http://freeapi.ipip.net/' + ip
    res = requests.get(url)
    print(res.json())
    for i in res.json():
        location = location + i
    return location


def statistics():
    addr_dict = {}
    file_name = 'peers.csv'
    with open(file_name, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        for row in reader:
            item = {}
            ip = row[0].split(':', 1)[0]
            if ip in addr_dict.keys():
                addr_dict[ip]['count'] = addr_dict[ip]['count'] + 1
            else:
                item['count'] = 1
                item['version'] = row[1]
                item['location'] = get_ip_location(ip)
                addr_dict[ip] = item

    file_name = 'nodes.csv'
    with open(file_name, 'a', newline='') as csv_file:
        file_header = ['ip', 'count', 'version', 'location']
        writer = csv.writer(csv_file)
        writer.writerow(file_header)

        for key in addr_dict.keys():
            writer.writerow([key, addr_dict[key]['count'], addr_dict[key]['version'], addr_dict[key]['location']])


# get_peer_info()
# statistics()
