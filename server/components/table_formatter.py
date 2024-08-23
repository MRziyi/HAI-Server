import asyncio
import json
import os
import re
import panel as pn

import global_vars

class Formatter():
    def __init__(self,is_warmup) -> None:
        self.is_warmup=is_warmup

    async def generate_tables(self,text):
        if(text==''):
            return
        if(self.is_warmup):
            format="{"+f'''
    "travel_table":"{global_vars.warmup_table}",
    '''+"}"
        else:
            format="{"+f'''
    "sightseeing_table":"{global_vars.sightseeing_table}",
    "dining_table":"{global_vars.dining_table}",
    "budget_table":"{global_vars.budget_table}"
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
        else:
            json_content=raw_tables
        try:
            tables = json.loads(json_content)
            result = {"tables": []}
            if "travel_table" in tables:
                content = tables["travel_table"]
                if content != "None":
                    result["tables"].append({
                        "name": "travel_table",
                        "content": content
                    })
            else:
                for table_name, content in tables.items():
                    if content != "None":
                        result["tables"].append({
                            "name": table_name,
                            "content": content
                        })
            global_vars.execute_core.send_to_client("solution/table/update",result)
                
        except json.JSONDecodeError as e:
            print(f"解析失败：\n原始输出：\n{raw_tables}\n错误：{e}")

