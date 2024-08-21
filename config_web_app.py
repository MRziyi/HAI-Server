import panel as pn
import global_vars
from pages.welcome_page.welcome_page import WelcomePage

pn.extension()

# 创建 Panel 服务器
def init_web_page():
    welcome = WelcomePage()
    global_vars.app_layout[:] = [welcome]
    global_vars.app = pn.template.VanillaTemplate(title='POLARIS')
    global_vars.app.main.append(global_vars.app_layout)
    global_vars.app.modal.append(global_vars.modal_content)

init_web_page()
global_vars.app.servable()