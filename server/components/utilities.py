import asyncio
import json
import re
from typing import Sequence, AsyncGenerator
from autogen_agentchat.messages import TextMessage, ChatMessage, AgentEvent
from autogen_agentchat.base import Response
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken

import global_vars

class VAgent(AssistantAgent):
    async def on_messages_stream(
        self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[AgentEvent | ChatMessage | Response, None]:
        async for msg in super().on_messages_stream(messages, cancellation_token):
            # 先保持原有消息流
            yield msg
            
            # 仅处理最终响应消息
            if isinstance(msg, Response):
                chat_msg = msg.chat_message
                if chat_msg.source != 'User':  # 确保是当前Agent生成的消息
                    print(f"----CATCHED---- {chat_msg.source}: {chat_msg.content}")
                    print_message_callback(chat_msg.source,chat_msg.content)

# class VAgent(AssistantAgent):
    
#     async def on_messages_stream(
#         self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken
#     ) -> AsyncGenerator[AgentEvent | ChatMessage | Response, None]:
#         # 保持原有功能
#         async for msg in super().on_messages_stream(messages, cancellation_token):
#             # 额外功能：调用 print_message_callback
#             if messages:  # 确保 messages 不为空
#                 print("----CATCHED----print_message_callback: "+messages[-1].source+'\n'+messages[-1].content+'---------')
#                 if(messages[-1].source!='User'):
#                     print_message_callback(self.name, messages[-1].source, messages[-1].content)
            
#             yield msg  # 保持原来 yield 的消息


def print_message_callback(sender_name, massage):
    try:
        data = json.loads(massage)
    except json.JSONDecodeError as e:
        print("----------Failed to decode ProcessManager JSON:--------\n", e)
        print(f"Content: {massage}\n-----------------\n")
        data = {}

    recipient_name=data.get('target', None)
    massage_content = data.get('answer', None)

    if(sender_name=="ProcessManager"):
        current_step = data.get('current_step', None)
        if current_step:
            global_vars.execute_core.send_to_client("process/update",
                    {
                        "current_step":current_step
                    })


    print(f"Messages from: {sender_name} sent to: {recipient_name} | message: {massage_content}")
    if(len(massage_content) < 200):
        print_chat_message(recipient_name,sender_name, massage_content)
    else:
        print("-----format_and_print_message Called from: "+sender_name)
        asyncio.create_task(format_and_print_message(recipient_name, sender_name, massage))
    return False, None


def print_chat_message(recipient_name,sender_name, message):
   
    global_vars.execute_core.send_to_client("agent/talk",
                {
                    "from":sender_name,
                    "to":recipient_name,
                    "chat":f'{message}'
                })
    
    print("-------Unformatted Chat Content--------")
    print(f'{recipient_name}, {message}')
    print("-------------")

def selector_func(messages: Sequence[AgentEvent | ChatMessage]) -> str | None:
    json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
    json_match = json_pattern.search(messages[-1].content)
    if json_match:
        json_content = json_match.group(1)
    else:
        json_content = messages[-1].content
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        print("----------Failed to decode JSON:--------\n", e)
        print(f"Content: {messages[-1].content}\n-----------------\n")
        data = {}

    target_name = data.get('target', None)
    if target_name:
        if target_name =="User":
            global_vars.req_ans_agent_name=messages[-1].source
        print("Selector Choose:"+ target_name)
        return target_name
    else:
        print("Target Agent Parse Error:"+json_content)
        return "ProcessManager"


    # User input function used by the team.
async def get_user_input(prompt: str, cancellation_token: CancellationToken | None) -> str:
        print('--getting human input--')  # or however you wish to display the prompt
        global_vars.execute_core.send_to_client("agent/req_ans",
                {
                    "from":global_vars.req_ans_agent_name,
                })
        # Create a new Future object for this input operation if none exists
        if global_vars.input_future is None or global_vars.input_future.done():
            global_vars.input_future = asyncio.Future()

        # Wait for the callback to set a result on the future
        await global_vars.input_future

        # Once the result is set, extract the value and reset the future for the next input operation
        input_value = global_vars.input_future.result()
        global_vars.input_future = None
        return input_value

async def format_and_print_message(recipient_name, sender_name, massage):

    global_vars.execute_core.send_to_client("agent/prepare_whiteboard",
            {
                "agent_name":sender_name,
            })

    cancellation_token = CancellationToken()
    formatted_reply = await global_vars.global_formatter.on_messages([
        TextMessage(source='user',content=f'''Determine if the content in the <text> tag fits typical short conversational exchanges:
<text>
{massage}
</text>'''+'''

1. If the content is a short conversation (less then 4 sentence), output according to the structure in <colloquialInputExample>:

<colloquialInputExample>
{
  "chat": "short conversational content"
}
</colloquialInputExample>

Note:
- Only use the `chat` field; do not include other fields.

2. If the content is too long, split it into two parts: `chat` and `content`:
   - `chat`: Short conversational exchange (e.g., question, brief thoughts, next step, etc.)
   - `content`: Detailed context for `chat` (e.g., tasks, proposals, or plans). Use Markdown format.

The formatted output should follow the structure in <formalInputExample>:

<formalInputExample>
{
  "chat": "short conversational content",
  "content": "longer plan or list of issues displayed in Markdown format"
}
</formalInputExample>

Note:
- Only use the `chat` and `content` fields; do not include other fields.
- The `content` field should be the original content of the agent's full output after removing the `chat` portion, without adding or omitting any information.

The output should follow the above format and be returned as JSON.''')],
cancellation_token=cancellation_token
    )

    try:
        data = json.loads(formatted_reply.chat_message.content)
    except json.JSONDecodeError as e:
        print("----------Failed to decode JSON:--------\n", e)
        print(f"Content: {formatted_reply}\n-----------------\n")
        data = {}

    chat_content = data.get('chat', None)
    if chat_content:
        print_chat_message(recipient_name,sender_name, chat_content)
        
    md_content = data.get('content', None)
    if md_content:
        print("-------Formatted MD Content--------")
        print(md_content)
        print("-------------")
        
        global_vars.execute_core.send_to_client("solution/panel/update",
                {
                    "solution":md_content,
                    "agent_name":sender_name
                })
