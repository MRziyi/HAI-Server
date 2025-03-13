import asyncio
import json
from typing import Optional
import global_vars
from server.components.utilities import VAgent, get_user_input, print_message_callback, selector_func
from server.components.websocket_manager import WebSocketManager

from autogen_agentchat.conditions import  TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.base import TaskResult

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.agents import BaseChatAgent
from autogen_agentchat.agents import AssistantAgent

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

    def init_agent_list(self) -> list[BaseChatAgent]:
        agent_list=[]
        # Generate Introductions for each agent
        agents_intro="User: Human User, Administrator\n"
        for agent_info in self.agents:
            agents_intro+=f"{agent_info['name']}: {agent_info['system_message']}\n"

        for agent_info in self.agents:
            if(agent_info['name']=="ProcessManager"):
                system_message=f'''You are ProcessManager, responsible for managing task execution progress, assigning tasks to Agents, coordinating efforts, and communicating with users.
You need to:
- Assign tasks, guide progress, and coordinate with team members and the human user based on the team member descriptions in the `<teamMember>` tag.
- Use the task steps provided in the `<steps>` tag to determine the current task progress:

<teamMember>
{agents_intro}</teamMember>

<steps>
{self.steps}
</steps>

Important:
- Always communicate in Chinese.
- You are **forbidden** to proceed to the next step on your own. After completing one step, you **must** ask the user for approval before proceeding to the next step.
- Your responsibility is to manage task execution progress and assign tasks to Agents. You are **forbidden** from executing tasks yourself.
- When you need to summarize or when the user requests a summary, you must strictly refer to the entire context and ensure that all information is fully preserved. Generate a detailed and comprehensive integration of the content. Formatting adjustments are allowed, but no summarization or omissions.

Output Format:
- In the target field, based on the team member descriptions in the <teamMember> tag, specify the appropriate interaction recipient.
    - If delegating tasks, seeking advice, or communicating with another Agent, specify the Agent's name.
    - If further thinking is required, specify yourself again.
    - Specify User if you need to advance the task's next step, ask questions or gather more information
- In the `answer` field, provide the content you want to communicate with the target team member.
- In the `current_step` field, determine and specify the current task step based on the context.
Follow the JSON format.'''
                agent = VAgent(
                    name="ProcessManager",
                    model_client=global_vars.cached_process_manager_model,
                    description="Manages task progress, assigns tasks to Agents, coordinating efforts, and communicates with users.",
                    system_message=system_message,)
            else:
                system_message=f"""You are {agent_info['name']}, {agent_info['system_message']}.
Important:
- Always communicate in Chinese.
- As shown in the `<teamMember>` tag, you are collaborating with other Agents to solve the user's problem. The task breakdown is provided in the `<steps>` tag.  
- Focus only on your designated responsibilities and complete them to the best of your ability. Other team mate will handle their specialized tasks, with `ProcessManager` coordinating team collaboration.  

<teamMember>
{agents_intro}</teamMember>

<steps>
{self.steps}
</steps>
"""
                # if not self.is_web:
                system_message+="""
Task Execution Rules:
- You are **forbidden** from completing the entire step at once. You must first gather ENOUGH background information and user preferences, then discuss the plan step-by-step with the user. You must interact with User AT LEAST THREE ROUNDs.
- Since the user has no experience with the task, you need to ask **inspiring** questions to uncover implicit constraints or user needs. These questions should help the user explore and complete the task in a detailed and comprehensive way, such as:
  - Additional information needed to solve the problem
  - Potential user needs or overlooked requirements
- If multiple options exist during the planning process, you cannot make decisions on your own. Provide sufficient background information and ask the user for their input.  
- You must actively recommend options to the user with specific and real information. Do not fabricate or create content."""             
                if self.is_single:
                    system_message+="""

Output Format:
- In the `target` field, If you need user input or additional information, set User. If further thinking is required, set yourself. 
- In the `answer` field, provide the content you want to communicate with User."""
                else:
                    system_message+=f"""
                    
Output Format:
- In the `target` field, based on the team member descriptions in the `<teamMember>` tag, specify the appropriate interaction recipient:  
  - **In most cases, set `User`** to gather additional information, refine the task iteratively, stimulate the user's thinking, and understand their preferences, choices, and decisions. Your primary role is to **collaborate iteratively** with the user to complete task planning.  
  - If delegating tasks, seeking advice, or communicating with another Agent, set the Agent's name.  
  - If further thinking is required, set yourself.  
  - If your specialized task is complete **or you want to advance the task's next step**, interact with `ProcessManager` to coordinate progress.  
- In the `answer` field, provide the content you want to communicate with the target team member."""
                    
                agent = VAgent(
                    name=agent_info['name'],
                    model_client=global_vars.cached_agent_model,
                    description=f"{agent_info['system_message']}",
                    system_message=system_message)
            agent_list.append(agent)

        agent_list.append(UserProxyAgent("User",
            input_func=get_user_input))
        
        return agent_list
    
    def __init__(self, ws_manager:WebSocketManager,is_single:bool,is_web:bool):
        self.is_single=is_single
        self.is_web=is_web
        self.ws_manager=ws_manager
        if is_single:
            self.init_config('config/config_single.json')
        else:   
            self.init_config('config/config.json')

        self.send_to_client("config/info",
                    {
                        "task_name":self.task_name,
                        "task_req":self.task_req,
                        "agent_list":self.agents,
                        "step_list":self.steps
                    })
        
        termination = TextMentionTermination("TERMINATE")
        agent_list = self.init_agent_list()
        self.team = SelectorGroupChat(agent_list,
            model_client=global_vars.smaller_model,
            termination_condition=termination,
            allow_repeated_speaker=True,
            selector_func=selector_func,
        )

    def send_to_client(self, type, data):
        asyncio.create_task(self.ws_manager.send_to_client_queue.put(json.dumps(
            {
                "type": type,
                "data": data
            },ensure_ascii=False, indent=4)))
        self.ws_manager.log(type,json.dumps(data,ensure_ascii=False))
        

        
    def start_chat(self,target='',answer=''):
        if target=='' and answer=='':
            global_vars.chat_task = asyncio.create_task(self.run_team_stream('ProcessManager',f"{self.task_name}: {self.task_req}"))if not self.is_single else asyncio.create_task(self.run_team_stream(self.agents[0]['name'],f"{self.task_name}: {self.task_req}"))
        else:
            global_vars.chat_task = asyncio.create_task(self.run_team_stream(target,answer))



    async def run_team_stream(self,target,answer) -> None:
        async for message in self.team.run_stream(task=TextMessage(source='User',content=json.dumps(
                    {
                        "target": target,
                        "answer": answer
                    },ensure_ascii=False,indent=4))):
            if isinstance(message, TaskResult):
                print("Stop Reason:", message.stop_reason)
            # else:
            #     print(message)
