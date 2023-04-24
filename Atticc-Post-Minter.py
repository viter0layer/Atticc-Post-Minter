import random
import time
import requests
import inspect
from datetime import datetime
from web3 import Web3
from eth_account.messages import encode_defunct
from colorama import init, Fore
from random import choice
init()

gwei = 1.4 # Check current minimum gwei in BNB chain - https://t.me/BSC_gwei_checker
rpcs = ['https://bsc.blockpi.network/v1/rpc/public', 'https://rpc.ankr.com/bsc', 'https://bsc.rpc.blxrbdn.com']
bscscan_api = 'bscscan API'
last_hash = ''

abi = [{"inputs": [{"internalType": "address", "name": "_logic", "type": "address"},{"internalType": "bytes", "name": "_data", "type": "bytes"}], "stateMutability": "payable", "type": "constructor"}, {"anonymous": False, "inputs": [{"indexed": False, "internalType": "address", "name": "previousAdmin", "type": "address"},{"indexed": False, "internalType": "address", "name": "newAdmin", "type": "address"}], "name": "AdminChanged", "type": "event"}, {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "beacon", "type": "address"}], "name": "BeaconUpgraded", "type": "event"}, {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "implementation", "type": "address"}], "name": "Upgraded", "type": "event"}, {"stateMutability": "payable", "type": "fallback"}, {"stateMutability": "payable", "type": "receive"}]
contract_address = '0x2723522702093601e6360CAe665518C4f63e9dA6'

web3_rpc = [Web3(Web3.HTTPProvider(rpc)) for rpc in rpcs]
errors = []
hashes = {}
colors = [Fore.GREEN, Fore.BLUE, Fore.RED]


def read_file(caller):
    if caller == 'create_essence':
        private_message = {}
        with open('private message.txt', 'r') as file:
            for line in file.readlines():
                p, m = line.replace('\n', '').split(':')
                private_message[p] = m
        if private_message == {} or private_message == {'private': 'message'}:
            print(Fore.RED + 'Неправильные данные в private message.txt. Пожалуйста, откройте файл и посмотрите формат' + Fore.RESET)
            input()
        return private_message

    elif caller == 'collect_essence':
        privates = []
        with open('privates.txt', 'r') as file:
            for line in file.readlines():
                privates.append(line.replace('\n', ''))
        if privates == [] or privates == ['private']:
            print(Fore.RED + 'Неправильные данные в private message.txt. Пожалуйста, откройте файл и посмотрите формат' + Fore.RESET)
            input()
        return privates


def to_hex(string: str):
    return string.encode('utf-8').hex()


def sign_signature(web3, private_key, message):
    message_hash = encode_defunct(text=message)
    signed_message = web3.eth.account.sign_message(message_hash, private_key)

    signature = signed_message.signature.hex()

    return signature


def get_bearer(web3, private, address):
    time_now = int(time.time()*1000)
    message = f'\nPurpose: Sign to verify wallet ownership in Atticc platform.\nWallet address: {address}\nNonce: {time_now}\n'
    signed_message = sign_signature(web3, private, message)

    headers = {
        'authority': 'atticc.xyz',
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://atticc.xyz',
        'referer': f'https://atticc.xyz/users/{address}/posts',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }

    json_data = {
        'signedMessage': signed_message,
        'message': message,
        'publicAddress': address,
    }

    response = requests.post('https://atticc.xyz/api/verify', headers=headers, json=json_data)

    return response.json()['token']


def create_post(address, bearer, message):
    headers = {
        'authority': 'query.dev.atticc.xyz',
        'accept': '*/*',
        'authorization': f'Bearer {bearer}',
        'content-type': 'application/json, application/json',
        'origin': 'https://atticc.xyz',
        'referer': 'https://atticc.xyz/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }

    data = f'{{"query":"\\n  mutation createPost(\\n    $description: String\\n    $address: String\\n    $imageUrl: String\\n    $communityAddress: String\\n    $tags: json\\n    $mentionedUsers: json\\n    $category: String\\n    $visibility: atticcdev_COMMUNITY_CATEGORY_enum\\n  ) {{\\n    insert_atticcdev_post_one(\\n      object: {{\\n        authorAddress: $address\\n        description: $description\\n        imageUrl: $imageUrl\\n        communityAddress: $communityAddress\\n        tags: $tags\\n        mentionedUsers: $mentionedUsers\\n        category: $category\\n        visibility: $visibility\\n      }}\\n    ) {{\\n      id\\n    }}\\n  }}\\n","variables":{{"address":"{address}","description":"{message}","communityAddress":null,"tags":"[]","mentionedUsers":"[]","category":null,"visibility":"Public"}},"operationName":"createPost"}}'

    response = requests.post('https://query.dev.atticc.xyz/v1/graphql', headers=headers, data=data)
    post_id = response.json()['data']['insert_atticcdev_post_one']['id']

    return post_id


def get_metadata(address, bearer, post_id):
    headers = {
        'authority': 'atticc.xyz',
        'accept': 'application/json',
        'authorization': f'Bearer {bearer}',
        'content-type': 'application/json',
        'origin': 'https://atticc.xyz',
        'referer': f'https://atticc.xyz/users/{address}/posts',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }

    json_data = {
        'filename': post_id + '-metadata',
        'ext': '.json',
    }

    response = requests.post('https://atticc.xyz/api/presigned-upload', headers=headers,
                             json=json_data)
    print(response.json())
    return response.json()


def request_to_amazon_server(amazon_link, address, post_id, message, key):
    unix_time = int(key.split('-')[-1].split('.')[0])/1000
    issue_date = datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    date = datetime.utcfromtimestamp(unix_time).strftime('%d.%m.%Y')
    print(key, issue_date, date)

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://atticc.xyz',
        'Referer': 'https://atticc.xyz/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }

    json_data = {
        'metadata_id': post_id,
        'version': '1.0.0',
        'app_id': 'atticc.xyz',
        'lang': 'en',
        'issue_date': issue_date,
        'description': message,
        'external_url': f'https://atticc.xyz/users/{address}/posts/{post_id}',
        'image': 'https://media.atticc.xyz/essence.png',
        'name': f'Post by {address} on Atticc at {date}'
    }

    response = requests.put(
        amazon_link,
        headers=headers,
        json=json_data,
    )
    print(response)


def get_hex_user_id(address, bearer):
    profile_id = None
    headers = {
        'authority': 'query.dev.atticc.xyz',
        'accept': '*/*',
        'authorization': f'Bearer {bearer}',
        'content-type': 'application/json, application/json',
        'origin': 'https://atticc.xyz',
        'referer': 'https://atticc.xyz/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }
    for i in range(10):
        data = '{"query":"\\nquery getPosts($addresses: [String], $postId: uuid, $communityAddress: String, $offset: Int = 0, $limit: Int = 10) {\\n    atticcdev_post(\\n      limit: $limit\\n      offset: $offset\\n      where: {\\n        _and: [\\n          \\n          { authorAddress: { _in: $addresses }}, \\n           \\n           \\n        ]\\n      }\\n      order_by: { pinned: desc, createdAt: desc  }\\n    ) {\\n      createdAt\\n      description\\n      id\\n      communityAddress\\n      essence\\n      community {\\n        address\\n        coverUrl\\n        name\\n        organizerAddress\\n        moderatorAddresses\\n      }\\n      tags\\n      mentionedUsers\\n      category\\n      visibility\\n      imageUrl\\n      postId\\n      title\\n      updatedAt\\n      pinned\\n      authorAddress\\n      post {\\n        id\\n        description\\n        imageUrl\\n        createdAt\\n        updatedAt\\n        authorAddress\\n        communityAddress\\n        visibility\\n        community {\\n          address\\n          coverUrl\\n          name\\n        }\\n      }\\n      author {\\n  address\\n  avatar\\n  domain\\n}\\n      likes(where: {action: {_eq: LIKE}}) {\\n  userAddress\\n}\\n      shares(where: {action: {_eq: SHARE}}) {\\n  userAddress\\n}\\n      likes_aggregate(where: {action: {_eq: LIKE}})  {\\n        aggregate {\\n          count\\n        }\\n      }\\n      shares_aggregate(where: {action: {_eq: SHARE}})  {\\n        aggregate {\\n          count\\n        }\\n      }\\n      comments_aggregate  {\\n        aggregate {\\n          count\\n        }\\n      }\\n      comments(limit: 50, order_by: { updatedAt: desc }, where: {replyId: {_is_null: true}}) {\\n        createdAt\\n        updatedAt\\n        id\\n        imageUrl\\n        likes_aggregate(where: {action: {_eq: LIKE}})  {\\n        aggregate {\\n          count\\n        }\\n      }\\n        post {\\n          id\\n          authorAddress\\n          communityAddress\\n        }\\n        likes(where: {action: {_eq: LIKE}}) {\\n  userAddress\\n}\\n        shares(where: {action: {_eq: SHARE}}) {\\n  userAddress\\n}\\n        shares_aggregate(where: {action: {_eq: SHARE}})  {\\n        aggregate {\\n          count\\n        }\\n      }\\n        replies(limit: 50, order_by: { updatedAt: asc }) {\\n          createdAt\\n          updatedAt\\n          id\\n          imageUrl\\n          likes_aggregate(where: {action: {_eq: LIKE}})  {\\n        aggregate {\\n          count\\n        }\\n      }\\n          likes(where: {action: {_eq: LIKE}}) {\\n  userAddress\\n}\\n          post {\\n            id\\n            authorAddress\\n            communityAddress\\n          }\\n          message\\n          replyId\\n          authorAddress\\n          author {\\n  address\\n  avatar\\n  domain\\n}\\n        }\\n        replies_aggregate  {\\n        aggregate {\\n          count\\n        }\\n      }\\n        message\\n        authorAddress\\n        author {\\n  address\\n  avatar\\n  domain\\n}\\n      }\\n    }\\n  }\\n","variables":{"addresses":["' + address + '"],"offset":' + f'{i*10}' + ',"limit":10},"operationName":"getPosts"}'

        response = requests.post('https://query.dev.atticc.xyz/v1/graphql', headers=headers, data=data)

        for i in response.json()['data']['atticcdev_post']:
            if i['essence'] == {}:
                continue
            else:
                print(i['essence'])
                profile_id = i['essence'].split(':')[-1].replace('}', '')
                break

        if profile_id:
            user_id = hex(int(profile_id))[2:]
            return user_id


def get_hex_ccprofile_id(address):
    headers = {
        'authority': 'bsc-mainnet.web3api.com',
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://bscscan.com',
        'referer': 'https://bscscan.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }

    json_data = {
        'jsonrpc': '2.0',
        'id': 2,
        'method': 'eth_call',
        'params': [
            {
                'from': '0x0000000000000000000000000000000000000000',
                'data': f'0xdfa52f07000000000000000000000000{address[2:]}',
                'to': '0x2723522702093601e6360cae665518c4f63e9da6',
            },
            'latest',
        ],
    }

    response = requests.post(
        'https://bsc-mainnet.web3api.com/v1/KBR2FY9IJ2IXESQMQ45X76BNWDAW2TT3Z3',
        headers=headers,
        json=json_data,
    )

    return response.json()['result'].split('0')[-1]


def format_data_register_essence(hex_user_id, hex_name, hex_essence_token_uri):
    return f'0x71fd0a98000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000002a000000000000000000000000000000000000000000000000000000000000{hex_user_id}00000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000016000000000000000000000000000000000000000000000000000000000000001a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000004a{hex_name}0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000034154500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008c{hex_essence_token_uri}000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000'


def format_data_collect_essence(address, hex_user_id):
    # return f'0xbe10bc61000000000000000000000000{address[2:]}00000000000000000000000000000000000000000000000000000000000{hex_user_id}000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000'
    return f'0xbe10bc61000000000000000000000000{address[2:]}0000000000000000000000000000000000000000000000000000000000013555000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000'


def mint(web3, address, private, data, gas, waiting=True):
    nonce = web3.eth.getTransactionCount(address)
    tx_create = web3.eth.account.sign_transaction({
        'to': contract_address,
        'value': 0,
        'gas': random.randint(gas[0], gas[1]),
        'gasPrice': web3.toWei(gwei, 'gwei'),
        'nonce': nonce,
        'data': data,
        'chainId': 56
    },
        private
    )
    tx_hash = web3.eth.sendRawTransaction(tx_create.rawTransaction)
    print(f"Transaction hash: {tx_hash.hex()}")
    with open('hashes.txt', 'a') as file:
        file.write(f'{tx_hash.hex()}\n')

    return tx_hash.hex()


def wait_tx(tx_hash):
    tmp = 0
    while True:
        if tmp >= 60:
            print('Transaction error')
            errors.append(private)
            break
        url = f"https://api.bscscan.com/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={bscscan_api}"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            status = data["result"]['status']
            if status == "1" or status == '0':
                break
        tmp += 1
        time.sleep(5)


def check_hashes():
    result = None
    caller = inspect.stack()[1][3]
    not_worked_out = {}

    for tx_hash in hashes.keys():
        tx_hash = tx_hash.replace('\n', '')

        url = f"https://api.bscscan.com/api?module=transaction&action=gettxreceiptstatus&txhash={tx_hash}&apikey={bscscan_api}"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            status = data["result"]['status']
            if status == "1":
                print(f"Транзакция успешно обработана: {tx_hash}")
            else:
                print(f"Транзакция не обработана: {tx_hash}")
                not_worked_out[tx_hash] = hashes[tx_hash]

    if caller == 'create_essence':
        result = {}
        for p, m in not_worked_out.values().items():
            result[p] = m
    elif caller == 'collect_essence':
        result = []
        for p in not_worked_out.values():
            result.append(p)

    if result:
        print(f'Wallets left: {len(result)}')
        return result
    else:
        colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
        goodbye = list("goodbye")

        for i in range(len(goodbye)):
            print(colors[i] + goodbye[i], end='')
        exit()


def create_essence(private_message: dict):
    i = 0
    global hashes
    global last_hash
    hashes.clear()
    for private, message in private_message.items():
        web3 = choice(web3_rpc)
        address = web3.eth.account.privateKeyToAccount(private).address
        print(f'{colors[i%2]}{address}:{private}')

        bearer = get_bearer(web3, private, address)
        post_id = create_post(address, bearer, message)
        post_info = get_metadata(address, bearer, post_id)
        request_to_amazon_server(post_info['url'], address, post_id, message, post_info['key'])
        link = 'https://media.atticc.xyz/' + post_info['key']
        metadata = requests.get(link).json()
        data_register_essence = format_data_register_essence(get_hex_user_id(address, bearer), to_hex(metadata['name']), to_hex(link))

        try:
            last_hash = mint(web3, address, private, data_register_essence, [750000, 820000], waiting=False)
            hashes[last_hash] = {private: message}
        except Exception as e:
            print(f'{colors[2]}{e}{colors[i%2]}')
            errors.append(private)

        i += 1
        time.sleep(5)

    wait_tx(last_hash)
    global gwei
    gwei = float(input('Enter gwei: '))
    create_essence(check_hashes())


def collect_essence(privates: list):
    i = 0
    global hashes
    global last_hash
    hashes.clear()
    for private in privates:
        web3 = web3_rpc[i % 5]
        address = web3.eth.account.privateKeyToAccount(private).address
        print(f'{colors[i % 2]}{address}:{private}')

        bearer = get_bearer(web3, private, address)
        data_collect_essence = format_data_collect_essence(address, get_hex_user_id(address, bearer))

        try:
            last_hash = mint(web3, address, private, data_collect_essence, [120000, 130000], waiting=False)
            hashes[last_hash] = private
        except Exception as e:
            print(f'{colors[2]}{e}{colors[i%2]}')
            errors.append(private)

        i += 1
        time.sleep(5)

    wait_tx(last_hash)
    global gwei
    gwei = float(input('Enter gwei: '))
    collect_essence(check_hashes())


def main():
    ask = int(input('Enter number: 1 or 2 \n[1] Create essence\n[2] Collect essence'))
    if ask == 1:
        create_essence(read_file(caller='create_essence'))
    elif ask == 2:
        collect_essence(read_file(caller='collect_essence'))
    else:
        print('Enter number: 1 or 2')


if __name__ == '__main__':
    main()

with open('errors.txt', 'w') as file:
    for private in errors:
        file.write(f'{private}\n')
