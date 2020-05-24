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
        stats = [0] * 6
        for user in USERS:
            value = DATA[user]
            stats[value] += 1
        return json.dumps({"type": "state", "states" : [stats[1], stats[2], stats[3], stats[4], stats[5]]})


def users_count():
    return json.dumps({"type": "users", "count": len(USERS)})


async def notify_state():
    if DATA:  # asyncio.wait doesn't accept an empty list
        message = get_stats()
        await asyncio.wait([user.send(message) for user in USERS])


async def notify_users():
    if DATA:  # asyncio.wait doesn't accept an empty list
        message = users_count()
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

async def alert():
    message = json.dumps({"type": "alert"})
    await asyncio.wait([user.send(message) for user in USERS])

async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(get_stats())
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "update":
                number = int(data["value"])
                if number >= 0 and number <= 5:
                    DATA[websocket] = number
                    await notify_state()
                else:
                    logging.error(data)

            elif data["type"] == "alert":
                await alert()
    finally:
        await unregister(websocket)


if __name__ == '__main__':
    start_server = websockets.serve(counter, "", 3015)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
