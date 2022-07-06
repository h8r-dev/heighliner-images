"""
该脚本用于将数据回传给 callback url.
"""

import os
import json
import requests

def main():
    callback_url = os.getenv('CALLBACK_URL')
    callback_token = os.getenv('CALLBACK_TOKEN')
    kubeconfig = open('./kubeconfig', 'r')
    kubeconfig = kubeconfig.read()
    ip = open('./ecs-ip.txt', 'r')
    ip = ip.read()
    instance_id = open('./ecs-id.txt', 'r')
    instance_id = instance_id.read()

    data = {
        "kubeconfig": kubeconfig,
        "ip": ip,
        "token": callback_token,
        "instance_id": instance_id,
        "region": "cn-hongkong",
    }

    print("Callback Url: {}".format(callback_url))
    print(data)

    res = requests.patch(callback_url, json=data)
    print('---------- Request callback url response ----------------')
    print(res.status_code)
    print(res.text)
    print('---------- Request callback url response ----------------')

if __name__ == '__main__':
    main()
