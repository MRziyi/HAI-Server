import asyncio
import json
from fastapi import FastAPI, WebSocket
import uvicorn

import global_vars
from server.components.websocket_manager import WebSocketManager
from server.execute_core import ExecuteCore

ws_app = FastAPI()



async def send_to_client_listener(ws_manager: WebSocketManager):
    while True:
        msg_to_send = await ws_manager.send_to_client_queue.get()
        await ws_manager.websocket.send_text(msg_to_send)
        # print("-----SEND TO WS------\n"+msg_to_send)
        await asyncio.sleep(0.05)

async def recv_from_client_listener(ws_manager: WebSocketManager):
    while True:
        raw_input = await ws_manager.websocket.receive_text()
        print("-----MSG FROM WS------\n"+raw_input)
        try:
            json_input = json.loads(raw_input)
            type = json_input.get("type")
            data = json_input.get("data")
            json_data = json.loads(data)
        except Exception as e:
            print("raw_data decode ERROR:", str(e))
            continue
        if type == "user/talk":
            text = json_data.get("content")
            target_agent_name = json_data.get("targetAgent")
            if text == '':
                return
            if global_vars.input_future and not global_vars.input_future.done() and global_vars.req_ans_agent_name == target_agent_name:
                global_vars.input_future.set_result(text)
            else:
                global_vars.chat_task.cancel()  # 取消任务
                user_proxy = global_vars.groupchat.agent_by_name("Admin")
                global_vars.chat_task = asyncio.create_task(user_proxy.a_initiate_chat(
                    recipient=global_vars.groupchat_manager,
                    message="@" + target_agent_name + "@, " + text,
                    clear_history=False
                ))
        elif type == "user/confirm_solution":
            text = json_data.get("solution")
            global_vars.execute_core.format_solution_to_table(text)
        elif type=="process/start_plan":
            if(global_vars.chat_task!=None):
                global_vars.chat_task.cancel()
            global_vars.execute_core.start_chat()
        elif type=="process/finish_warmup":
            del global_vars.execute_core
            global_vars.execute_core = ExecuteCore(ws_manager=ws_manager,config_url='config/sightseeing_config.txt')
        await asyncio.sleep(0.05)

@ws_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    ws_manager = WebSocketManager(websocket=websocket)
    await ws_manager.connect()
    try:
        # Start listeners as tasks
        send_task = asyncio.create_task(send_to_client_listener(ws_manager))
        recv_task = asyncio.create_task(recv_from_client_listener(ws_manager))
        
        global_vars.execute_core = ExecuteCore(ws_manager=ws_manager,config_url='config/warmup_config.txt')

        # Wait for both listeners and chat to complete
        await asyncio.gather(send_task, recv_task)
    except Exception as e:
        print("ERROR:", str(e))
    finally:
        await ws_manager.disconnect()

if __name__ == "__main__":
    uvicorn.run(ws_app, host="0.0.0.0", port=8000)
