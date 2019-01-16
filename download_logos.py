#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 从 newdex.io 下载 token logo
# 命名格式为symbol.png
# symbol为newdex的api返回的字段，比如21dice4token-tod-eos

import requests
import os
import json

root_path = '/home/bcd-root/dapp_logo/'
root_url = 'https://ndi.340wan.com/image/'


def get_token_names():
    response = requests.get('https://api.newdex.io/v1/common/symbols')
    response = json.loads(response.text)
    if response['code'] is 200:
        token_list = []
        for token in response['data']:
            if token['symbol'][-4:] == '-eos':
                token_list.append(token['symbol'][:-4])
    token_list.append('eosio.token-eos')
    return token_list


def download_logos():
    token_names = get_token_names()
    for token in token_names:
        image_name = token + '.png'
        image_path = root_path + 'eos.png' if image_name == 'eosio.token-eos.png' else root_path + image_name
        image_url = root_url + image_name
        response = requests.get(image_url)
        try:
            response.raise_for_status()
            if not os.path.exists(root_path):
                os.mkdir(root_path)
            if not os.path.exists(image_path):
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                print('image %s saved' % image_name)
            else:
                print('image %s exists' % image_name)
        except Exception as e:
            print('下载失败，图片地址:%s, Error:%s' % (image_url, e))


download_logos()
