import asyncio
import json
import re
import panel as pn
import param

import global_vars

class AgentList(pn.viewable.Viewer):
    agents = param.List(doc="A list of agents.")
    task_name =param.String(doc="Name of task")
    task_req = param.String(doc="Requirements of task")

    def __init__(self, **params):
        super().__init__(**params)
        self._layout = pn.Column(
            pn.pane.GIF('https://upload.wikimedia.org/wikipedia/commons/b/b1/Loading_icon.gif', sizing_mode='stretch_width'),
            "正在推荐合适的多Agent阵容..."
            )
        asyncio.create_task(self.generate_agent_list())

    async def generate_agent_list(self):
        raw_agent_list = await global_vars.global_assistant.a_generate_reply(messages=[{
        "role": "user",
        "name": "Admin",
        "content": f'''你需要为<task>标签内的任务推荐一个合适的多Agent阵容，
参考<example_task>标签的样例任务，以给出<example_output>标签内样例输出的格式进行回复，只需要回复json格式即可
<task>{self.task_name}: {self.task_req}</task>'''+
'''
<example_task>行程规划：我需要带领4人的团队前往东南大学参加学术会议，同时在南京知名景点参观。你需要考虑时间安排、交通、资金等全面的因素，并且每个团队成员有着不同的喜好和倾向。请权衡内容，制定平衡合理的行程安排</example_task>
<example_output>
[
    {
        "name": "BudgetAgent",
        "avatar": "💵",
        "system_message": "负责预算分配和控制，确保总花费在预算范围内。",
        "chinese_name":"预算专家"
    },
    {
        "name": "TrafficAgent",
        "avatar": "🚗",
        "system_message": "优化交通路线和工具，避免晕车问题，并提供方便的交通方式。",
        "chinese_name":"交通专家"
    },
    {
        "name": "DiningAgent",
        "avatar": "🍽️",
        "system_message": "安排每日餐饮，确保满足每个成员的饮食偏好。",
        "chinese_name":"餐饮专家"
    },
    {
        "name": "AccommodationAgent",
        "avatar": "🏨",
        "system_message": "安排酒店选择，权衡每个人的偏好和预算。",
        "chinese_name":"住宿专家"
    },
    {
        "name": "EntertainmentAgent",
        "avatar": "🎉",
        "system_message": "根据成员兴趣安排参观活动，确保每个人都有满意的活动安排，并且将时间安排与会议议程避开。",
        "chinese_name":"娱乐专家"
    }
]
    </example_output>
    
    注意：
    - name字段应该是英文大驼峰格式，avatar字段应该使用与这个Agent相关的emoji，chinese_name字段应该是中文名
    - 你需要根据任务要求决定Agent个数，最多不超过4个Agent'''
    }])
        try:
            self.agents = json.loads(raw_agent_list)
        except json.JSONDecodeError as e:
            self._layout.clear()
            self._layout = pn.Column(f"解析失败：\n原始输出：\n{raw_agent_list}\n错误：{e}")
        self.update_agents_list()


    def update_agents_list(self):
        self._layout.clear()
        for idx, agent in enumerate(self.agents):
            agent_info = f'## {agent["avatar"]} {agent["chinese_name"]}\n'
            agent_info += agent["system_message"] + "\n\n---\n\n"
            update_button = pn.widgets.Button(name="Update")
            update_button.on_click(lambda event, idx=idx: self.open_update_popup(idx))
            agent_panel = pn.Row(pn.pane.Markdown(agent_info,width=290), update_button)
            self._layout.append(agent_panel)
        
        add_agent_button = pn.widgets.Button(name='Add Agent')
        add_agent_button.on_click(self.open_add_popup)
        self._layout.append(add_agent_button)
        
    def open_update_popup(self, idx):

        def confirm_update(event):
            self.agents[idx] = {
                "name": name_input.value,
                "avatar": avatar_input.value,
                "system_message": system_message_input.value
            }
            self.update_agents_list()
            global_vars.app.close_modal()

        agent = self.agents[idx]
        name_input = pn.widgets.TextInput(name="Name", value=agent["name"])
        avatar_input = pn.widgets.TextInput(name="Avatar", value=agent["avatar"])
        system_message_input = pn.widgets.TextAreaInput(name="System Message", value=agent["system_message"])
        confirm_button = pn.widgets.Button(name="Confirm Update", button_type='primary')
        delete_button = pn.widgets.Button(name="Delete", button_type='danger', width=80)
        delete_button.on_click(lambda event, idx=idx: self.delete_agent(idx))
        
        confirm_button.on_click(confirm_update)
        popup_content = pn.Row(name_input, avatar_input, system_message_input)
        buttons = pn.Row(confirm_button, delete_button)
        global_vars.modal_content[:] = [popup_content,buttons]
        global_vars.app.open_modal()

    def get_agents(self):
        print(self.agents)
        return self.agents
        
    def open_add_popup(self, event):
        name_input = pn.widgets.TextInput(name="Name", value="")
        avatar_input = pn.widgets.TextInput(name="Avatar", value="")
        system_message_input = pn.widgets.TextAreaInput(name="System Message", value="")
        confirm_button = pn.widgets.Button(name="Confirm Add", button_type='primary')
        
        def confirm_add(event):
            self.agents.append({
                "name": name_input.value,
                "avatar": avatar_input.value,
                "system_message": system_message_input.value
            })
            self.update_agents_list()
            global_vars.app.close_modal()
        
        confirm_button.on_click(confirm_add)
        popup_content = pn.Column(name_input, avatar_input, system_message_input, confirm_button)
        popup_content = pn.Row(name_input, avatar_input, system_message_input)
        global_vars.modal_content[:] = [popup_content,confirm_button]
        global_vars.app.open_modal()

    def add_agent(self, event):
        self.update_agents_list()

    def delete_agent(self, idx):
        global_vars.app.close_modal()
        self.agents.pop(idx)
        self.update_agents_list()

    def __panel__(self):
        return self._layout