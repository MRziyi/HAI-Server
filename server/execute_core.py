import asyncio
import json
import re
from fastapi import WebSocket
import panel as pn
import param
import autogen
import uvicorn
import global_vars
from server.components.agents import MyConversableAgent, custom_speaker_selection_func, print_message_callback
from server.components.websocket_manager import WebSocketManager


class ExecuteCore():

    def init_config(self,config_url):
        try:
            with open(config_url, 'r') as f:  # 使用 'r' 模式读取文件
                text = f.read()
            results = json.loads(text)
            task_name = results.get("task_name")
            task_req = results.get("task_req")
            agent_list = results.get("agent_list")
            step_list = results.get("step_list")
        
            print('-------agent_list-------')
            print(agent_list)
            print('-------step_list-------')
            print(step_list)
            print('-----------------------')
        except FileNotFoundError:
            print("Chat history file not found!")
        except json.JSONDecodeError:
            print("Error decoding chat history!")

        self.agents=agent_list
        self.steps=step_list
        self.task_name=task_name
        self.task_req=task_req

    def init_agent_list(self) -> list[autogen.Agent]:
        agent_list=[]

        for agent_info in self.agents:
            if(agent_info['name']=="Critic"):
                agent =  autogen.AssistantAgent(
                name="Critic",
                description="你是Critic，需要再次检查其他Agent给出的任务计划、任务结果，并提出反馈",
                system_message="""你是Critic，需要再次检查其他Agent给出的任务计划、任务结果，并提出反馈
            重点：
            - 你的职责只是检查其他Agent给出的结果提出反馈，而不是帮他们修改内容
            - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
                - 你的输出应该是**一个**json格式的，应该包括如下例子中的参数：
                {
                    "chat":"较短的反馈，或对用户的提问"
                }
                - 你**只能**使用chat参数，前者用于较短内容，后者只用于较长的内容，你**禁止**自己编撰其他参数
                - 你**只能**输出一个json
            - 当你想向用户提问，或者希望获取更多信息时，你需要提及关键词“Admin”
            - 当你想与其他Agent交流/委托任务/寻求意见等时，你需要提及它的名字
                """,
                llm_config=global_vars.llm_config,
                human_input_mode="NEVER",
            )
            elif(agent_info['name']=="ProcessManager"):
                agent = autogen.AssistantAgent(
                name="ProcessManager",
                description="你是ProcessManager，负责管理任务执行进度，为Agent分配任务，或通过Admin向用户提问",
                system_message=f'你是ProcessManager，负责管理任务执行进度，为Agent分配任务，或通过Admin向用户提问 \n任务步骤：{self.steps}'+
    """
                重点：
                - 当你想向用户提问，或者希望获取更多信息时，你需要提及关键词“Admin”
                - 当你想与其他Agent交流/委托任务/寻求意见等时，你需要提及它的名字
                - 你**必须**频繁地通过Admin与用户交互
                - 你被**禁止**进行下一个任务，在一个任务结束后，你**必须**向用户提问，直到**批准**才可以进行下一步
                - 你的职责是管理任务执行进度、为Agent分配任务，你被**禁止**自己执行任务

                - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
                    输出格式：
                    - 你**只能**使用chat与current_step参数，你**禁止**自己编撰其他参数
                    {
                        "chat":"较短的自己的想法、或是下一步的打算"
                        "current_step":1 (当前进行的任务编号)
                    }
                    - 你**只能**输出一个json
                    - 你**必须**根据聊天记录判断当前任务进度执行到了哪一步，并通过"current_step"进行表示
                    - 在调整"current_step"时，你必须寻求Admin的意见，未经允许的修改将造成严重后果
    """,
                llm_config=global_vars.llm_config,
                human_input_mode="NEVER",
            )
            else:
                agent=autogen.AssistantAgent(
                    name=agent_info['name'],
                    description=f"你是{agent_info['name']}，{agent_info['system_message']}",
                    system_message=f"你是{agent_info['name']}，{agent_info['system_message']}"+
        """ 重点：
        - 请使用中文。
        - 当你想向用户提问，或者希望获取更多信息时，你需要提及关键词“Admin”
        - 当你想与其他Agent交流/委托任务/寻求意见等时，你需要提及它的名字
        - 你被**禁止**一次性完成计划，确保在进行计划之前获得足够详细的信息，进行计划时应与用户逐步讨论进行。
        - 规划过程中面对多个可选项时，你不能自己决定，应该询问用户的意见。
        - 在与用户讨论方案时，你应该提出**具有启发性**的细节问题，例如：对解决问题需要补充的细节信息、用户可能忽略的需求等。""",
                    llm_config=global_vars.llm_config,
                    human_input_mode="NEVER",
                )
            agent.register_reply(
                [autogen.Agent, None],
                reply_func=print_message_callback, 
                config={"callback": None},
            )

            agent_list.append(agent)
        return agent_list
    
    async def init_chat(self):

        user_proxy=MyConversableAgent(
            name="Admin",
            # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("exit"),
            system_message='''你是人类Admin''',
            code_execution_config=False,
            human_input_mode="ALWAYS",
        )
        user_proxy.register_reply(
            [autogen.Agent, None],
            reply_func=print_message_callback, 
            config={"callback": None},
        )
        agent_list = self.init_agent_list()
        agent_list.append(user_proxy)
        global_vars.groupchat = autogen.GroupChat(
            agents=agent_list, 
            speaker_selection_method=custom_speaker_selection_func,
            messages=[])
        global_vars.groupchat_manager = autogen.GroupChatManager(groupchat=global_vars.groupchat,system_message='''Group chat manager. 
重点：
- 你被**禁止**向不同的Agent询问相同的信息
- 当你想向用户提问，或者希望获取更多信息时，请通过Admin向用户提问
''', llm_config=global_vars.llm_config)

        await user_proxy.a_initiate_chat(global_vars.groupchat_manager, message=f"@ProcessManager@, {self.task_name}\n{self.task_req}")

    def __init__(self, ws_manager:WebSocketManager,config_url):
        self.init_config(config_url)
        self.ws_manager=ws_manager

        self.send_to_client("config/info",
                    {
                        "task_name":self.task_name,
                        "task_req":self.task_req,
                        "agent_list":self.agents,
                        "step_list":self.steps
                    })

    def send_to_client(self, type, data):
        asyncio.create_task(self.ws_manager.send_to_client_queue.put(json.dumps(
            {
                "type": type,
                "data": data
            },ensure_ascii=False, indent=4)))
        self.ws_manager.log(type+": "+str(data))
        

        
    def start_chat(self):
        global_vars.chat_task = asyncio.create_task(self.init_chat())