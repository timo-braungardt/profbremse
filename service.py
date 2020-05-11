#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets

from threading import RLock

logging.basicConfig()

DATA = dict()
data_lock = RLock()

USERS = set()
user_lock = RLock()

def get_stats():
    if DATA:
        stats = [0] * 6
        with user_lock, data_lock:
            for user in USERS:
                value = DATA[user]
                stats[value] += 1
        return json.dumps({"type": "state", "states" : stats[1:]})


def users_count():
    return json.dumps({"type": "users", "count": len(USERS)})


async def notify_users(message):
    if DATA:  # asyncio.wait doesn't accept an empty list
        message = users_count()
        await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
    USERS.add(websocket)
    DATA[websocket] = 4
    await notify_users(users_count())
    await notify_users(get_stats())


async def unregister(websocket):
    USERS.remove(websocket)
    DATA.pop(websocket)
    await notify_users(users_count())
    await notify_users(get_stats())


async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(get_stats())
        async for message in websocket:
            data = json.loads(message)
            number = int(data["value"])
            # check if number in [0..5]
            if number in range(0, 6):
                with data_lock:
                    DATA[websocket] = number
                await notify_users(get_stats())
            else:
                logging.error(data)
    finally:
        await unregister(websocket)


if __name__ == '__main__':
    start_server = websockets.serve(counter, "", 3015)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
