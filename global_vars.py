from dotenv import load_dotenv
import os
import panel as pn
import autogen

load_dotenv()  # 加载 .env 文件中的所有环境变量

app = None
app_layout= pn.Column("Modal")
modal_content = pn.Column("Modal")

input_future=None
chat_task=None
groupchat=None
groupchat_manager=None

execute_core=None
req_ans_agent_name=''



llm_config={"config_list": [
            {
                'model': 'gpt-4o-2024-08-06',
                "api_key": os.environ["OPENAI_API_KEY"],
                # "base_url":"https://azureport.eastus.cloudapp.azure.com "
            }
            ], 
            "temperature":0, 
            "timeout":3000,
            "seed": 53}

global_assistant= autogen.AssistantAgent(
            name='Assistant',
            llm_config=llm_config,
            human_input_mode="NEVER",
            system_message='你是Assistant，需要根据用户的要求，参考给出的例子给出json格式的输出',
        )
smaller_model_config={"config_list": [
            {
                'model': 'gpt-4o-mini',
                "api_key": os.environ["OPENAI_API_KEY"],
                # "base_url":"https://azureport.eastus.cloudapp.azure.com "
            }
            ], 
            "temperature":0, 
            "timeout":3000,
            "seed": 53}

global_formatter= autogen.AssistantAgent(
            name='Formatter',
            llm_config=smaller_model_config,
            human_input_mode="NEVER",
            system_message='''你是Formatter，需要将输入的内容，按照用户要求给出json格式的输出''',
        )

speaker_selector= autogen.AssistantAgent(
            name='SpeakerSelector',
            llm_config=smaller_model_config,
            human_input_mode="NEVER",
            system_message='''You are in a role play game. The roles in <roles_info> are available. Read the message in <message>. Then select the next role from <role_list> to play. Only return the role name (pure string).''',
        )

warmup_table="""| 日期   | 景点安排 | 餐饮安排 |
| 第一天  |        |          |
| 第二天  |          |          |
""" 

sightseeing_table="""| 日期    | 时间 | 李教授 | 陈教授 | 张博士 | 王同学 |
| 6月30日 | 下午 |(具体的会议活动或观光安排，如参加开幕式或牛首山观光)|(这张表中不应该填写餐饮相关内容)|       |       |
|         | 晚上 |       |       |       |       |
| 7月1日  | 上午 |       |       |       |       |
|         | 下午 |       |       |       |       |
|         | 晚上 |       |       |       |       |
| 7月2日  | 上午 |       |       |       |       |
|         | 下午 |       |       |       |       |
|         | 晚上 |       |       |       |       |
| 7月3日  | 上午 |       |       |       |       |
|         | 下午 |       |       |       |       |
|         | 晚上 |       |       |       |       |
| 7月4日  | 上午 |       |       |       |       |
|         | 下午 |       |       |       |       |
|         | 晚上 |       |       |       |       |
| 7月5日  | 上午 |       |       |       |       |
|         | 下午 |       |       |       |       |
|         | 晚上 |       |       |       |       |
"""
dining_table="""| 日期    | 时间 | 李教授 | 陈教授 | 张博士 | 王同学 |
| 6月30日 | 晚餐 |(具体的餐饮安排，如在夫子庙品尝小吃)|       |       |       |
| 7月1日  | 午餐 |       |       |       |       |
|         | 晚餐 |       |       |       |       |
| 7月2日  | 午餐 |       |       |       |       |
|         | 晚餐 |       |       |       |       |
| 7月3日  | 午餐 |       |       |       |       |
|         | 晚餐 |       |       |       |       |
| 7月4日  | 午餐 |       |       |       |       |
|         | 晚餐 |       |       |       |       |
| 7月5日  | 午餐 |       |       |       |       |
|         | 晚餐 |       |       |       |       |
"""
budget_table="""| 成员   | 预期预算 | 餐饮开销 | 门票开销 | 交通开销 | 合计开销 |
| 李教授  |(具体的金额)|          |          |          |          |
| 陈教授  |          |          |          |          |          |
| 张博士  |          |          |          |          |          |
| 王同学  |          |          |          |          |          |
"""