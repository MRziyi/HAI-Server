import asyncio
from fastapi import WebSocket
import global_vars


class WebSocketManager:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.send_to_client_queue = asyncio.Queue()

    async def connect(self):
        await self.websocket.accept()
        print("WS Connected!")

    async def disconnect(self):
        if(global_vars.chat_task!=None):
            global_vars.chat_task.cancel()
        print("WS Disconnected")