import asyncio
import json
import os
import re
import panel as pn

import global_vars

class Formatter():
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

    async def generate_tables(self,text):
        if(text==''):
            return
        format="{"+f'''
    "sightseeing_table":"{self.sightseeing_table}",
    "dining_table":"{self.dining_table}",
    "budget_table":"{self.budget_table}"
    '''+"}"
        raw_tables = await global_vars.global_assistant.a_generate_reply(messages=[{
        "role": "user",
        "name": "Admin",
        "content": f'''你需要将<content>标签内的内容进行格式化，将内容填充到<format>标签内的表格中。
        注意：
        * 你不能额外为表格添加<content>标签内没有的信息
        * 你不能省略任何<content>标签内给出的信息，你需要把这些信息全部都详细地填充到表格中
        * 对于未指定特定成员的安排，默认为全部成员都参与，即需要为所有人填写
        * 你需要按照<format>标签内的格式回复进行格式化的内容，只需要回复json格式即可
        * <format>标签内存在冗余的表格，当<content>并未提及相关内容时，这个表格不应该被填写或是输出，它应该被输出为"None"，比如:"sightseeing_table":"None"或"dining_table":"None"或"budget_table":"None"，你被**禁止**擅自补充信息。
    <content>{text}</content>
    <format>
{format}
    </format>'''
    }])
        # 使用正则表达式提取 JSON 内容
        print(raw_tables)
        json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
        json_match = json_pattern.search(raw_tables)
        if json_match:
            json_content = json_match.group(1)
            try:
                tables = json.loads(json_content)
                global_vars.execute_core.send_to_client("solution/table/update",tables)
                
            except json.JSONDecodeError as e:
                print(f"解析失败：\n原始输出：\n{raw_tables}\n错误：{e}")

