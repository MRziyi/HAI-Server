import json
import param
import panel as pn

from panel.viewable import Viewer
import global_vars
from pages.config_page.components.agent_list import AgentList
from pages.config_page.components.step_list import StepList

pn.extension()  # for notebook

class ConfigPage(Viewer):
    task_name = param.String()

    def __init__(self, **params):
        super().__init__(**params)

        self.req_input = pn.widgets.TextAreaInput(
            name=f'任务：{self.task_name}', 
            auto_grow=True, 
            max_rows=10, 
            rows=6, 
            placeholder="任务已知的详细信息/要求/约束",
            sizing_mode='stretch_width',
            value='''我需要带领4人的团队前往东南大学参加学术会议，同时在南京知名景点参观。你需要考虑观光与学术会议的时间安排、餐饮、资金等全面的因素，并且每个团队成员有着不同的喜好和倾向。请权衡以下内容，制定平衡合理的观光计划、餐饮安排与预算计划。
- 地点：东南大学，南京。
- 议程：
  - 6月30日
    - 确认住宿和交通安排。
    - 准备会议用品和服装。
  - 7月1日
    - 上午报到，下午参加开幕式。
    - 确认第二天的汇报安排。
  - 7月2日
    - 下午进行汇报。
  - 7月3日-7月4日
    - 上午可选参观展板或进行学术交流。
  - 7月5日
    - 晚上参加闭幕式。
- 成员情况：
  - 李教授：资深学者，注重学术交流和会议活动，对观光兴趣不大，年纪较大，腿脚不便，喜欢高档住宿饮食，预算3000元。
  - 陈教授：喜欢文化艺术，注重文化体验，对紫外线过敏，不喜欢室外活动，预算2500元。
  - 张博士：环保主义者，关注可持续发展，对自然景点和生态园区感兴趣，晕车，酒精过敏，喜欢体验当地特色，预算2000元。
  - 王同学：年轻科研人员，预算有限，喜欢探索新事物新科技，四川人喜欢吃辣。希望既能参加学术活动，又能参观南京的知名景点，预算1500元。
- 住宿情况：集体住宿于南京上秦淮假日酒店。
''')
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(self.req_confirm)
        
        self.req_content = pn.Column(
            "## 请输入任务详细信息/要求/约束",
            self.req_input,
            confirm_button
        )
        req_card = pn.Card(self.req_content, title='详细信息', max_width=400)

        self.agent_list_content = pn.Column("# 请首先确认任务的详细信息/要求/约束")
        agent_card = pn.Card(self.agent_list_content, title='Agents分配', margin=(0, 20), max_width=400)

        self.step_list_content = pn.Column("# 请首先确认任务的Agents分配")
        step_card = pn.Card(self.step_list_content, title='步骤配置', max_width=400)

        self._layout = pn.Row(req_card, agent_card, step_card)

    def req_confirm(self, event):
        confirmed_req = f"## 任务「{self.task_name}」的详细信息\n{self.req_input.value}"
        self.req_content[:] = [confirmed_req]
        
        agent_list_content = AgentList(task_name=self.task_name,task_req=self.req_input.value)
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(lambda event, agent_list_content=agent_list_content: self.agents_confirm(agent_list_content))
        
        self.agent_list_content[:] = [agent_list_content, confirm_button]
    
    def agents_confirm(self, agent_list_content):
        agent_list=agent_list_content.get_agents()
        agent_list.insert(0,{"name": "ProcessManager", "avatar": "⏩️", "system_message": "负责管理任务执行进度，为Agent分配任务，或通过Admin向用户提问"})
        confirmed_agents = f"## 任务「{self.task_name}」的Agents分配\n"
        for agent in agent_list:
            confirmed_agents += f'## {agent["avatar"]} {agent["name"]}\n'
            confirmed_agents += agent["system_message"] + "\n\n---\n\n"
        
        step_list_content = StepList(agents=agent_list,task_name=self.task_name,task_req=self.req_input.value)
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(lambda event, step_list_content=step_list_content: self.steps_confirm(step_list_content))

        self.agent_list_content[:] = [confirmed_agents]
        self.step_list_content[:] = [step_list_content,confirm_button]

    
    def steps_confirm(self,step_list_content):
        agent_list,step_list=step_list_content.get_lists()
        try:
            with open('config/sightseeing_config.txt', 'w') as f:  # 使用 'w' 模式写入文件
                f.write(json.dumps(
                    {
                        "task_name":self.task_name,
                        "task_req":self.req_input.value,
                        "agent_list":agent_list,
                        "step_list":step_list
                    },ensure_ascii=False,indent=4))
            print("Config exported!")
        except Exception as e:
            print(f"Error exporting config history: {e}")
        
        global_vars.app_layout[:] = ["WebSocket服务待启用，请前往VR进行体验"]

    def __panel__(self):
        return self._layout

