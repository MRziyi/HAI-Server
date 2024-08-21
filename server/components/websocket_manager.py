import asyncio
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.send_to_client_queue = asyncio.Queue()
        self.recv_from_client_queue = asyncio.Queue()

    async def connect(self):
        await self.websocket.accept()
        print("WS Connected!")

    async def disconnect(self):
        self.recv_from_client_queue.put_nowait("DO_FINISH")
        print("WS Disconnected")