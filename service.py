#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets

logging.basicConfig()

DATA = dict()

USERS = set()

def get_stats():
    if DATA:
        stats = [0] * 7
        for user in USERS:
            value = DATA[user]
            stats[value] += 1
        return json.dumps({"type": "state", "ei":stats[1], "zw":stats[2], "dr":stats[3], "vi":stats[4], "fu":stats[5], "se":stats[6]})

def state_event(websocket):
    return json.dumps({"type": "state", "value":DATA[websocket]})


def users_event():
    return json.dumps({"type": "users", "count": len(USERS)})


async def notify_state():
    if DATA:  # asyncio.wait doesn't accept an empty list
        message = get_stats()
        await asyncio.wait([user.send(message) for user in USERS])


async def notify_users():
    if DATA:  # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
    USERS.add(websocket)
    DATA[websocket] = 4
    await notify_users()
    await notify_state()


async def unregister(websocket):
    USERS.remove(websocket)
    DATA.pop(websocket)
    await notify_users()
    await notify_state()


async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(get_stats())
        async for message in websocket:
            data = json.loads(message)
            number = int(data["value"])
            if number >= 0 and number <= 5:
                DATA[websocket] = number
                await notify_state()
            else:
                logging.error(data)
    finally:
        await unregister(websocket)


start_server = websockets.serve(counter, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()