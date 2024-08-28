import json
import re
from typing import Literal, Union
import autogen
import asyncio
import global_vars


class MyConversableAgent(autogen.ConversableAgent):
    async def a_get_human_input(self, prompt: str) -> str:
        
        print('--getting human input--')  # or however you wish to display the prompt
        global_vars.execute_core.send_to_client("agent/req_ans",
                {
                    "from":global_vars.groupchat.messages[-1].get('name')
                })
        global_vars.req_ans_agent_name=self.name
        # Create a new Future object for this input operation if none exists
        if global_vars.input_future is None or global_vars.input_future.done():
            global_vars.input_future = asyncio.Future()

        # Wait for the callback to set a result on the future
        await global_vars.input_future

        # Once the result is set, extract the value and reset the future for the next input operation
        input_value = global_vars.input_future.result()
        global_vars.input_future = None
        return input_value


def print_message_callback(recipient, messages, sender, config):
    if "callback" in config and  config["callback"] is not None:
        callback = config["callback"]
        callback(sender, recipient, messages[-1])
    last_message = messages[-1]
    sender_name = last_message.get('name',None) or recipient.name
    print(f"Messages from: {sender_name} sent to: {recipient.name} | num messages: {len(messages)} | message: {last_message}")
    if(sender_name=="Admin"):
        return False, None
    elif(sender_name=="Critic" or sender_name=="ProcessManager" or len(last_message.get('content')) < 30):
        print_formatted_message(recipient.name, last_message)
    else:
        print("-----format_and_print_message Called from: "+sender_name)
        asyncio.create_task(format_and_print_message(recipient.name, last_message))
    return False, None

def print_formatted_message(recipient_name, message):
    content = message.get('content', '')
    sender_name = message.get('name', None) or recipient_name
    json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
    json_match = json_pattern.search(content)
    if json_match:
        json_content = json_match.group(1)
    else:
        json_content = content
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        print("----------Failed to decode JSON:--------\n", e)
        print(f"Content: {content}\n-----------------\n")
        data = {}
    
    chat_content = data.get('chat', None)
    current_step = data.get('current_step', None)

    if current_step:
        global_vars.execute_core.send_to_client("process/update",
                {
                    "current_step":current_step
                })

    message_content = chat_content or content
    global_vars.execute_core.send_to_client("agent/talk",
                {
                    "from":sender_name,
                    "to":recipient_name,
                    "chat":f'{recipient_name}, {message_content}' if 'name' in message else message_content
                })
    
    print("-------Unformatted Chat Content--------")
    print(f'{recipient_name}, {message_content}' if 'name' in message else message_content)
    print("-------------")


async def format_and_print_message(recipient_name, message):
    content = message.get('content', '')
    sender_name = message.get('name', None) or recipient_name
    formatted_reply = await global_vars.global_formatter.a_generate_reply(messages=[{
        "role": "user",
        "name": "Admin",
        "content": f'''将 <text> 标签中的内容拆分为两部分：一部分是较短的内容，如提问、简短的想法或下一步打算，另一部分是较长的内容，如详细的任务、提议或计划。格式化后的输出应符合 <example> 标签中例子的结构。
具体要求是：
- chat: 包含 <text> 中的提问、简短的想法或下一步的打算，不超过40字。
- content: 包含具体的较长内容，使用 Markdown 格式。如果内容少于 3 个句子，则输出 None。
<text>
{content}
</text>'''+'''
<example>
{
    "chat":"请问：1. 您是否有特定的景点或活动已经在考虑之中？谢谢！"
    "content":"None",
}
</example>

- 你**只能**使用chat与content参数，你**禁止**自己编撰其他参数
- 你**只能**输出一个json
- 你必须忠实地还原<content>标签内的信息，不能额外添加或编写<content>标签内没有的信息，也不能省略任何给出的信息。'''
    }])
    # 使用正则表达式提取 JSON 内容
    json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
    json_match = json_pattern.search(formatted_reply)
    if json_match:
        json_content = json_match.group(1)
    else:
        json_content = formatted_reply
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        print("----------Failed to decode JSON:--------\n", e)
        print(f"Content: {content}\n-----------------\n")
        data = {}

    chat_content = data.get('chat', None)
    md_content = data.get('content', None)
    print("-------Formatted MD Content--------")
    print(md_content)
    print("-------------")
    if md_content and md_content!="None":
        global_vars.execute_core.send_to_client("solution/panel/update",
                {
                    "solution":md_content
                })

    message_content = chat_content or content

    print("-------Formatted Chat Content--------")
    print(f'{recipient_name}, {message_content}' if 'name' in message else message_content)
    print("-------------")

    global_vars.execute_core.send_to_client("agent/talk",
                {
                    "from":sender_name,
                    "to":recipient_name,
                    "chat":f'{recipient_name}, {message_content}' if 'name' in message else message_content
                })



def custom_speaker_selection_func(
    last_speaker: autogen.Agent, 
    groupchat: autogen.GroupChat
) -> Union[autogen.Agent, Literal['auto', 'manual', 'random' 'round_robin'], None]:
    print(f'------custom_speaker_selection from：{last_speaker.name}------')
    agents=groupchat.agents
    roles = [agent.name+": "+agent.description for agent in agents]
    agentlist = [agent.name for agent in agents]

    message=groupchat.messages[-1].get('content')

    agent_name=''
    if(last_speaker.name=="Admin"):
        match = re.match(r"@([^@]+)@", message)
        if match:
            agent_name = match.group(1)
        print("NEXT SPEAKER: "+agent_name+", Previous is: Admin")
    else:
        agent_name = global_vars.speaker_selector.generate_reply(messages=[{
        "role": "user",
        "name": "Admin",
        "content": f'''<role_info>
{roles}
</role_info>

<message>
From: {last_speaker.name}
Content: {message}
</message>

<role_list>
{agentlist}
</role_list>

Note: 
- If the message is asking for information or decision, you can only select "Admin"
- If the message mentions other agents\' name (e.g. 我将委托EntertainmentAgent), select him'''}])
        print("NEXT SPEAKER: "+agent_name+", Previous is: "+last_speaker.name+'\n--------')
    next_agent=groupchat.agent_by_name(agent_name)
    if(next_agent is None):
        print("!!!next_agent is None!!! AUTO CHOOSE")
        return 'auto'
    else:
        return next_agent