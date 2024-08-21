import json
import panel as pn
import param
import autogen
import global_vars
from pages.config_page.config_page import ConfigPage


class WelcomePage(pn.viewable.Viewer):

    def switch_to_config_page(self,event):
        config_page = ConfigPage(task_name=self.text_input.value)
        global_vars.app_layout[:] = [config_page]  # 更新布局为 config 页面
    
    def __init__(self, **params):
        self.text_input = pn.widgets.TextInput(name='请问您想解决什么问题？',value="行程规划")
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')

        # 绑定按钮点击事件
        confirm_button.on_click(self.switch_to_config_page)

        # 初始布局为 welcome 页面
        self._layout = pn.Column('# 欢迎来到 POLARIS',
            pn.Row(
                self.text_input,
                confirm_button
            ))
    
    def __panel__(self):
        return self._layout
    