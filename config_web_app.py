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
    task_name = '旅行规划：百元挑战'
    task_req = '我想要与我的朋友一同在南京进行观光，旅行时间是9月10日-9月12日共3天，我需要根据自己与朋友的喜好，考虑时间安排、交通、餐饮、住宿、预算等重要的因素，制定平衡合理的行程安排。我们参加了百元挑战：我与好友每天的预算仅共有100元（不包含住宿），请尽可能设计丰富有趣的计划。“一张毛爷爷都不够吃个网红菜”，“地铁一天也得20块？”，“不要门票的景点才不赖”——预算的限制可能改变您原有的旅行风格，但是也会带来意想不到的趣味，请尽可能挖掘系统的潜力，毕竟这么困难的任务不找帮手怎么行？"'
    
    config = ConfigPage(task_name=task_name,task_req=task_req)
    global_vars.app_layout[:] = [config]
    global_vars.app.main.append(global_vars.app_layout)
    global_vars.app.modal.append(global_vars.modal_content)

init_web_page()
global_vars.app.servable()