import sys
import panel as pn
import global_vars
from pages.config_page.config_page import ConfigPage

pn.extension()

t1='我与好友想要前往上海分别参加一个展会，在展会时间外我们也想到一同在上海进行观光，请根据我与好友的喜好，考虑时间安排、交通、餐饮、住宿、预算等因素，制定平衡合理无冲突的行程安排。'
t1_selection=['''China Joy科技博览会
- 时间：9月10日 10:00 - 18:00
- 地点：上海新国际博览中心
''',
'''Bilibili World动漫展
- 时间：9月10日 14:00 - 20:00
- 地点：国家会展中心
''',
'''国际艺术博览会
- 时间：9月10日 13:00 - 20:00
- 地点：上海艺术中心
''',
'''国际美食节
- 时间：9月11日 12:00 - 19:00
- 地点：上海展览中心
''',
'''现代家居展览会
- 时间：9月11日 10:00 - 18:00
- 地点：上海家居博览馆
''',
'''健康与健身博览会
- 时间：9月11日 09:00 - 17:00
- 地点：世博展览馆
''',
'''国际时装周
- 时间：9月11日 15:00 - 22:00
- 地点：上海时尚中心
''']

t2='我与好友想要前往北京分别参加一个展会，在展会时间外我们也想到一同在北京进行观光，请根据我与好友的喜好，考虑时间安排、交通、餐饮、住宿、预算等因素，制定平衡合理无冲突的行程安排。'
t2_selection=['''中国数字娱乐博览会
- 时间：9月10日 10:00 - 18:00
- 地点：北京国家会议中心
''',
'''北京动漫游戏嘉年华
- 时间：9月10日 14:00 - 20:00
- 地点：北京展览馆
''',
'''北京国际艺术博览会
- 时间：9月10日 13:00 - 20:00
- 地点：中国国际展览中心(旧馆)
''',
'''国际美食节：
- 时间：9月11日 12:00 - 19:00
- 地点：北京农业展览馆
''',
'''现代家居展览会
- 时间：9月11日 10:00 - 18:00
- 地点：北京家居博览中心
''',
'''健康与健身博览会
- 时间：9月11日 09:00 - 17:00
- 地点：中国国际展览中心(新馆)
''',
'''国际时装周
- 时间：9月11日 15:00 - 22:00
- 地点：北京751D·PARK北京时尚设计广场
''']

# 创建 Panel 服务器
def init_web_page():
    task_req=''
    print(str(sys.argv))
    if sys.argv[1]=='t1':
        task_req=t1
        task_req+='\n我要参加的展会是：'+t1_selection[int(sys.argv[2])-1]
        task_req+='\n好友要参加的展会是：'+t1_selection[int(sys.argv[3])-1]
    else:
        task_req=t2
        task_req+='\n我要参加的展会是：'+t2_selection[int(sys.argv[2])-1]
        task_req+='\n好友要参加的展会是：'+t2_selection[int(sys.argv[3])-1]

    config = ConfigPage(task_name='旅行规划',task_req=task_req)
    global_vars.app_layout[:] = [config]
    global_vars.app = pn.template.VanillaTemplate(title='POLARIS')
    global_vars.app.main.append(global_vars.app_layout)
    global_vars.app.modal.append(global_vars.modal_content)

init_web_page()
global_vars.app.servable()