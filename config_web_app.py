import sys
import panel as pn
import global_vars
from pages.config_page.config_page import ConfigPage

pn.extension()

css = """
#input{
  font-size: 120%;
}
"""
pn.extension(raw_css=[css])

# 创建 Panel 服务器
def init_web_page():
    task_name = '旅行规划'
    task_req = '我想要与我的朋友一同在【目标城市】进行为期【n】天的旅行，制定行程安排'
    config = ConfigPage(task_name=task_name,task_req=task_req)
    global_vars.app_layout[:] = [config]
    global_vars.app.main.append(global_vars.app_layout)
    global_vars.app.modal.append(global_vars.modal_content)

init_web_page()
global_vars.app.servable()