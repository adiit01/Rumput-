import asyncio
import datetime
import json
import random
import ssl
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
import pyfiglet

logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=''),
    format=(
        "<green>{time:DD/MM/YY HH:mm:ss}</green> | "
        "<level>{level:8} | {message}</level>"
    ),
    colorize=True
)
ONETIME_PROXY = 100
extension_node_version = "4.26.2"
desktop_node_version = "4.30.0"

# Read UID and Proxy count
def read_uid_and_proxy():
    with open('userid.txt', 'r') as file:
        uid_count = sum(1 for line in file)

    with open('proxy.txt', 'r') as file:
        proxy_count = sum(1 for line in file)

    return uid_count, proxy_count

uid_count, proxy_count = read_uid_and_proxy()

print()
print(f"🔑 UID: {uid_count}.")
print(f"🌐 Loaded {proxy_count} proxies.")
print(f"🌐 Active proxy loaded per-task: {ONETIME_PROXY} proxies.")
print()

# Ask user for node type (extension or desktop)
# Automatically return "no" for get_user_input
def get_user_input():
    return False  # 'no' corresponds to False

remove_on_all_errors = get_user_input()

# Automatically return "desktop" for get_node_type
def get_node_type():
    return "desktop"

node_type = get_node_type()
print(f"🔵 {node_type.capitalize()} node. ENJOY!\n")

def truncate_userid(user_id):
    return f"{user_id[:4]}--{user_id[-4:]}"

def truncate_proxy(proxy):
    return f"{proxy[:6]}--{proxy[-10:]}"

async def connect_to_wss(protocol_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, protocol_proxy))
    logger.info(f"User ID: {truncate_userid(user_id)} | Device ID: {device_id} | Proxy: {truncate_proxy(protocol_proxy)}")

    while True:
        try:
            await asyncio.sleep(random.uniform(0.1, 1.0))  # reduced frequency
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
                "Mozilla/5.0 (Macintosh; ARM Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            ]
            custom_headers = {
                "User-Agent": random.choice(user_agents)
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy2.wynd.network:4444/", "wss://proxy2.wynd.network:4650/"]
            uri = random.choice(urilist)
            proxy = Proxy.from_url(protocol_proxy)

            if node_type == 'desktop':
                async with proxy_connect(
                    uri,
                    proxy=proxy,
                    ssl=ssl_context,
                    extra_headers={"User-Agent": custom_headers["User-Agent"]}
                ) as websocket:
                    logger.success(f"User ID: {truncate_userid(user_id)} | Successfully connected to WebSocket with Proxy: {truncate_proxy(protocol_proxy)}")

                    async def send_ping():
                        while True:
                            send_message = json.dumps({
                                "id": str(uuid.uuid4()),
                                "version": "1.0.0",
                                "action": "PING",
                                "data": {}
                            })
                            logger.debug(f"User ID: {truncate_userid(user_id)} | Sending PING message ID: {json.loads(send_message)['id']}")
                            await websocket.send(send_message)
                            rand_sleep = random.uniform(10, 30)  # random delay + reduce bandwidth usage
                            logger.info(f"User ID: {truncate_userid(user_id)} | Sleeping for {rand_sleep:.2f} seconds")
                            await asyncio.sleep(rand_sleep)

                    send_ping_task = asyncio.create_task(send_ping())

                    try:
                        while True:
                            response = await websocket.recv()
                            message = json.loads(response)
                            simply_message = {
                                'id': message.get('id'),
                                'action': message.get('action')
                            }
                            logger.info(f"User ID: {truncate_userid(user_id)} | Received message: {simply_message}")

                            custom_date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

                            if message.get("action") == "AUTH":
                                auth_response = {
                                    "id": message["id"],
                                    "origin_action": "AUTH",
                                    "result": {
                                        "browser_id": device_id,
                                        "user_id": user_id,
                                        "user_agent": custom_headers['User-Agent'],
                                        "timestamp": int(time.time()),
                                        "device_type": "desktop",
                                        "version": desktop_node_version
                                    }
                                }
                                logger.debug(f"User ID: {truncate_userid(user_id)} | Sending AUTH response ID: {auth_response['id']} | version: {auth_response['result']['version']}")
                                await websocket.send(json.dumps(auth_response))
                                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully authenticated with Device ID: {device_id}")
                            elif message.get("action") == "PONG":
                                pong_response = {"id": message["id"], "origin_action": "PONG"}
                                logger.debug(f"User ID: {truncate_userid(user_id)} | Sending PONG response: {pong_response}")
                                await websocket.send(json.dumps(pong_response))
                                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully sent PONG response ID: {pong_response['id']} | Action: {pong_response['origin_action']}")
                            elif message.get("action") == "HTTP_REQUEST":
                                http_request_response = {"id": message["id"], "origin_action": "HTTP_REQUEST"}
                                logger.debug(f"User ID: {truncate_userid(user_id)} | Sending HTTP_REQUEST response: {http_request_response}")
                                await websocket.send(json.dumps(http_request_response))
                                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully sent HTTP_REQUEST response ID: {http_request_response['id']} | Action: {http_request_response['origin_action']}")
                            elif message.get("action") == "OPEN_TUNNEL":
                                opentunnel_request_response = {
                                    "id": message["id"],
                                    "origin_action": "OPEN_TUNNEL",
                                    "result": {
                                        "url": message["url"],
                                        "status": 200,
                                        "status_text": "OK",
                                        "headers": {
                                            "content-type": "application/json; charset=utf-8",
                                            "date": custom_date,
                                            "keep-alive": "timeout=5",
                                            "proxy-connection": "keep-alive",
                                            "x-powered-by": "Express",
                                        }
                                    }
                                }
                                logger.debug(f"User ID: {truncate_userid(user_id)} | Sending OPEN_TUNNEL response: {opentunnel_request_response}")
                                await websocket.send(json.dumps(opentunnel_request_response))
                                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully sent OPEN_TUNNEL response ID: {opentunnel_request_response['id']} | Action: {opentunnel_request_response['origin_action']}")
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.error(f"User ID: {truncate_userid(user_id)} | WebSocket closed unexpectedly | Proxy: {truncate_proxy(protocol_proxy)} | Error: {str(e)[:30]}**")
                    finally:
                        await websocket.close()
                        logger.warning(f"User ID: {truncate_userid(user_id)} | WebSocket connection closed | Proxy: {truncate_proxy(protocol_proxy)}")
                        send_ping_task.cancel()
                        break

            elif node_type == 'extension':
                async with proxy_connect(
                    uri,
                    proxy=proxy,
                    ssl=ssl_context,
                    extra_headers={"Origin": "chrome-extension://ilehaonighjijnmpnagapkhpcdbhclfg", "User-Agent": custom_headers["User-Agent"]}
                ) as websocket:
                    logger.success(f"User ID: {truncate_userid(user_id)} | Successfully connected to WebSocket with Proxy: {truncate_proxy(protocol_proxy)}")

                    async def send_ping():
                        while True:
                            send_message = json.dumps({
                                "id": str(uuid.uuid4()),
                                "version": "1.0.0",
                                "action": "PING",
                                "data": {}
                            })
                            logger.debug(f"User ID: {truncate_userid(user_id)} | Sending PING message ID: {json.loads(send_message)['id']}")
                            await websocket.send(send_message)
                            rand_sleep = random.uniform(10, 30)  # random delay + reduce bandwidth usage
                            logger.info(f"User ID: {truncate_userid(user_id)} | Sleeping for {rand_sleep:.2f} seconds")
                            await asyncio.sleep(rand_sleep)

                    send_ping_task = asyncio.create_task(send_ping())

                    try:
                        while True:
                            response = await websocket.recv()
                            message = json.loads(response)
                            simply_message = {
                                'id': message.get('id'),
                                'action': message.get('action')
                            }
                            logger.info(f"User ID: {truncate_userid(user_id)} | Received message: {simply_message}")

                            custom_date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

                            if message.get("action") == "AUTH":
                                auth_response = {
                                    "id": message["id"],
                                    "origin_action": "AUTH",
                                    "result": {
                                        "browser_id": device_id,
                                        "user_id": user_id,
                                        "user_agent": custom_headers['User-Agent'],
                                        "timestamp": int(time.time()),
                                        "device_type": "extension",
                                        "version": extension_node_version,
                                        "extension_id": "ilehaonighjijnmpnagapkhpcdbhclfg"
                                    }
                                }
                                logger.debug(f"User ID: {truncate_userid(user_id)} | Sending AUTH response ID: {auth_response['id']} | version: {auth_response['result']['version']}")
                                await websocket.send(json.dumps(auth_response))
                                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully authenticated with Device ID: {device_id}")
                            elif message.get("action") == "PONG":
                                pong_response = {"id": message["id"], "origin_action": "PONG"}
                                logger.debug(f"User ID: {truncate_userid(user_id)} | Sending PONG response: {pong_response}")
                                await websocket.send(json.dumps(pong_response))
                                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully sent PONG response ID: {pong_response['id']} | Action: {pong_response['origin_action']}")
                            elif message.get("action") == "HTTP_REQUEST":
                                http_request_response = {"id": message["id"], "origin_action": "HTTP_REQUEST"}
                                logger.debug(f"User ID: {truncate_userid(user_id)} | Sending HTTP_REQUEST response: {http_request_response}")
                                await websocket.send(json.dumps(http_request_response))
                                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully sent HTTP_REQUEST response ID: {http_request_response['id']} | Action: {http_request_response['origin_action']}")
                            elif message.get("action") == "OPEN_TUNNEL":
                                opentunnel_request_response = {
                                    "id": message["id"],
                                    "origin_action": "OPEN_TUNNEL",
                                    "result": {
                                        "url": message["url"],
                                        "status": 200,
                                        "status_text": "OK",
                                        "headers": {
                                            "content-type": "application/json; charset=utf-8",
                                            "date": custom_date,
                                            "keep-alive": "timeout=5",
                                            "proxy-connection": "keep-alive",
                                            "x-powered-by": "Express",
                                        }
                                    }
                                }
                                logger.debug(f"User ID: {truncate_userid(user_id)} | Sending OPEN_TUNNEL response: {opentunnel_request_response}")
                                await websocket.send(json.dumps(opentunnel_request_response))
                                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully sent OPEN_TUNNEL response ID: {opentunnel_request_response['id']} | Action: {opentunnel_request_response['origin_action']}")
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.error(f"User ID: {truncate_userid(user_id)} | WebSocket closed unexpectedly | Proxy: {truncate_proxy(protocol_proxy)} | Error: {str(e)[:30]}**")
                    finally:
                        await websocket.close()
                        logger.warning(f"User ID: {truncate_userid(user_id)} | WebSocket connection closed | Proxy: {truncate_proxy(protocol_proxy)}")
                        send_ping_task.cancel()
                        break

        except Exception as e:
            logger.error(f"User ID: {truncate_userid(user_id)} | Error with proxy {truncate_proxy(protocol_proxy)} ➜ {str(e)[:30]}**")
            error_conditions = [
                "Host unreachable",
                "[SSL: WRONG_VERSION_NUMBER]", 
                "invalid length of packed IP address string", 
                "Empty connect reply",
                "Device creation limit exceeded",
                "[Errno 111] Could not connect to proxy",
                "sent 1011 (internal error) keepalive ping timeout; no close frame received"
            ]

            if remove_on_all_errors:
                if any(error_msg in str(e) for error_msg in error_conditions):
                    logger.warning(f"User ID: {truncate_userid(user_id)} | Removing error proxy from the list ➜ {truncate_proxy(protocol_proxy)}")
                    remove_proxy_from_list(protocol_proxy)
                    return None
            else:
                if "Device creation limit exceeded" in str(e):
                    logger.warning(f"User ID: {truncate_userid(user_id)} | Removing error proxy from the list ➜ {truncate_proxy(protocol_proxy)}")
                    remove_proxy_from_list(protocol_proxy)
                    return None
            continue

async def main():
    with open('userid.txt', 'r') as file:
        user_ids = file.read().splitlines()

    with open('proxy.txt', 'r') as file:
        all_proxies = file.read().splitlines()

    used_proxies = min(ONETIME_PROXY, len(all_proxies))
    active_proxies = random.sample(all_proxies, used_proxies)

    tasks = {}

    for user_id in user_ids:
        for proxy in active_proxies:
            await asyncio.sleep(random.uniform(1.2, 3.0))
            task = asyncio.create_task(connect_to_wss(proxy, user_id))
            tasks[task] = (proxy, user_id)

    while True:
        done, pending = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task.result() is None:
                failed_proxy, user_id = tasks[task]
                logger.warning(f"User ID: {truncate_userid(user_id)} | Removing and replacing failed proxy: {truncate_proxy(failed_proxy)}")

                if failed_proxy in active_proxies:
                    active_proxies.remove(failed_proxy)

                new_proxy = random.choice(all_proxies)
                active_proxies.append(new_proxy)

                await asyncio.sleep(random.uniform(1.2, 3.0))
                new_task = asyncio.create_task(connect_to_wss(new_proxy, user_id))
                tasks[new_task] = (new_proxy, user_id)
                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully replaced failed proxy: {truncate_proxy(failed_proxy)} with: {truncate_proxy(new_proxy)}")

            tasks.pop(task)

        for proxy in set(active_proxies) - {task[0] for task in tasks.values()}:
            for user_id in user_ids:
                await asyncio.sleep(random.uniform(1.2, 3.0))
                new_task = asyncio.create_task(connect_to_wss(proxy, user_id))
                tasks[new_task] = (proxy, user_id)
                logger.success(f"User ID: {truncate_userid(user_id)} | Successfully started task with proxy: {truncate_proxy(proxy)}")

def remove_proxy_from_list(proxy):
    with open("proxy.txt", "r+") as file:
        lines = file.readlines()
        file.seek(0)
        for line in lines:
            if line.strip() != proxy:
                file.write(line)
        file.truncate()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info(f"Program terminated by user. ENJOY!\n")
