import sys
import panel as pn
import global_vars
from pages.config_page.config_page import ConfigPage

pn.extension()

# 创建 Panel 服务器
def init_web_page():
    config = ConfigPage(task_name=sys.argv[1],task_req='')
    global_vars.app_layout[:] = [config]
    global_vars.app = pn.template.VanillaTemplate(title='POLARIS')
    global_vars.app.main.append(global_vars.app_layout)
    global_vars.app.modal.append(global_vars.modal_content)

init_web_page()
global_vars.app.servable()