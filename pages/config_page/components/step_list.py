import asyncio
import json
import re
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
import panel as pn
import param

import global_vars

class StepList(pn.viewable.Viewer):
    agents = param.List(doc="A list of agents.")
    steps = param.List(doc="A list of tasks.")
    task_name =param.String(doc="Name of task")
    task_req = param.String(doc="Requirements of task")
    
    
    def __init__(self, **params):
        super().__init__(**params)
        self._layout = pn.Column(
            pn.pane.GIF('https://upload.wikimedia.org/wikipedia/commons/b/b1/Loading_icon.gif', sizing_mode='stretch_width'),
            "正在推荐合适的步骤..."
            )
        asyncio.create_task(self.generate_step_list())

    async def generate_step_list(self):
        cancellation_token = CancellationToken()
        raw_step_list = await global_vars.global_assistant.on_messages([
            TextMessage(source='user',content=f'''You need to recommend appropriate steps for the task described in the <task> tag and match every relevant agent from the <agents> tag to each step. Please refer to the example task in the <example_task> tag and respond using the format provided in the <example_output> tag. Only return the JSON format.

Important:
1. 每个步骤需体现"约束网络"特性，展示该步骤涉及的多个约束专家之间的协作关系
2. 使用"协调X与Y的冲突"、"平衡A对B的影响"等表述反映约束间的动态权衡
3. 每个步骤必须包含至少2个相关领域Agent的协作说明

<task>{self.task_name}: {self.task_req}</task>
<agents>{self.agents}</agents>

<example_task>辩论材料准备：我需要为"人性本恶"主题的辩论准备材料</example_task>'''+'''

<example_output>
[
    {
        "name": "核心概念界定",
        "content": "定义专家（伦理维度）与哲学专家协作，协调'恶'的伦理定义与哲学基础之间的关联，法律专家将同步验证定义的法律适用性"
    },
    {
        "name": "论点网络构建",
        "content": "论点专家建立主张树时，历史专家提供案例支持，伦理专家确保主张合法性，矛盾协调员持续监测论点间的潜在冲突"
    },
    {
        "name": "反方预判矩阵",
        "content": "反驳专家联合心理学专家预测对方策略，经济专家评估论点经济影响，风险控制员标记高风险反驳点"
    },
    {
        "name": "动态平衡验证",
        "content": "逻辑专家协调哲学严谨性与现实可行性，伦理-法律双专家小组确保主张边界，优化专家进行最终权重调整"
    }
]
</example_output>

Note: Ensure that the `name` and `content` fields are in Chinese.</prompt>''')], cancellation_token=cancellation_token
        )

        json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
        json_match = json_pattern.search(raw_step_list.chat_message.content)
        if json_match:
            json_content = json_match.group(1)
        else:
            json_content = raw_step_list.chat_message.content
        try:
            self.steps = json.loads(json_content)
        except json.JSONDecodeError as e:
            self._layout.clear()
            self._layout = pn.Column(f"解析失败：\n原始输出：\n{raw_step_list.chat_message.content}\n错误：{e}")
        self.update_step_list()

    def get_lists(self):
        print(self.agents)
        return self.agents,self.steps

    def update_step_list(self):
        self._layout.clear()
        for idx, step in enumerate(self.steps):
            step_info = f'## {idx+1}. {step["name"]}\n'
            step_info += step["content"] + "\n\n---\n\n"
            edit_button = pn.widgets.Button(name="Edit")
            edit_button.on_click(lambda event, idx=idx: self.open_edit_modal(idx))
            
            step_panel = pn.Row(pn.pane.Markdown(step_info,width=290), edit_button)
            self._layout.append(step_panel)
        
        add_step_button = pn.widgets.Button(name='Add Step')
        add_step_button.on_click(self.open_add_modal)
        self._layout.append(add_step_button)
        
    def open_edit_modal(self, idx):
        def confirm_update(event):
            self.steps[idx] = {
                "name": name_input.value,
                "content": content_input.value
            }
            self.update_step_list()
            global_vars.app.close_modal()

        step = self.steps[idx]
        name_input = pn.widgets.TextInput(name="步骤名", value=step["name"])
        content_input = pn.widgets.TextInput(name="步骤内容", value=step["content"])
        confirm_button = pn.widgets.Button(name="Confirm Edit", button_type='primary')
        delete_button = pn.widgets.Button(name="Delete", button_type='danger')
        delete_button.on_click(lambda event, idx=idx: self.delete_step(idx))
        
        confirm_button.on_click(confirm_update)
        modal_content = pn.Row(name_input, content_input)
        buttons = pn.Row(confirm_button, delete_button)
        global_vars.modal_content[:] = [modal_content,buttons]
        global_vars.app.open_modal()


        
    def open_add_modal(self, event):
        name_input = pn.widgets.TextInput(name="Name", value="")
        avatar_input = pn.widgets.TextInput(name="Avatar", value="")
        system_message_input = pn.widgets.TextAreaInput(name="System Message", value="")
        confirm_button = pn.widgets.Button(name="Confirm Add", button_type='primary')
        
        def confirm_add(event):
            self.steps.append({
                "name": name_input.value,
                "content": content_input.value
            })
            self.update_step_list()
            global_vars.app.close_modal()
        
        name_input = pn.widgets.TextInput(name="步骤名")
        content_input = pn.widgets.TextInput(name="步骤内容")
        confirm_button.on_click(confirm_add)
        modal_content = pn.Row(name_input, content_input)
        global_vars.modal_content[:] = [modal_content,confirm_button]
        global_vars.app.open_modal()

    def delete_step(self, idx):
        global_vars.app.close_modal()
        self.steps.pop(idx)
        self.update_step_list()

    def __panel__(self):
        return self._layout