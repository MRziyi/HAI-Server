#!/usr/bin/env python3
import os
import csv
import json
from datetime import datetime

def parse_time(time_str):
    """
    解析 HH:MM:SS 格式的时间字符串
    """
    return datetime.strptime(time_str, '%H:%M:%S')

def process_file(tsv_path, md_path, group_type):
    # 统计指标初始化
    user_talk_count = 0
    total_content_length = 0
    process_start_time = None
    last_time = None
    agent_list = []
    step_list = []
    agent_conv_counts = {}  # 用于统计 targetAgent 出现次数

    # 构造 Markdown 内容，增加组别真实类型输出
    md_lines = []
    md_lines.append("# Solution")

    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f,quoting=csv.QUOTE_NONE, delimiter='\t')
        for row in reader:
            if len(row) < 3:
                continue
            time_str = row[0].strip().strip('"')
            log_type = row[1].strip().strip('"')
            detail_info_raw = row[2]


            if detail_info_raw.startswith('"') and detail_info_raw.endswith('"'):
                detail_info_raw = detail_info_raw[1:-1]
            try:
                detail_info = json.loads(detail_info_raw)
                # 如果解析结果还是字符串，则再解析一次
                if isinstance(detail_info, str):
                    detail_info = json.loads(detail_info)
            except Exception as e:
                detail_info = {}
            except Exception as e:
                detail_info = {}

            try:
                current_time = parse_time(time_str)
                last_time = current_time
            except Exception as e:
                current_time = None

            if log_type == "user/talk":
                user_talk_count += 1

                print(detail_info)
                print("-----")
                content = detail_info.get("content", "")
                total_content_length += len(content)
                target_agent = detail_info.get("targetAgent")
                if target_agent:
                    agent_conv_counts[target_agent] = agent_conv_counts.get(target_agent, 0) + 1

            elif log_type == 'process/update':
                # 获取当前步骤索引
                current_step = detail_info.get("current_step")
                current_step -=1
                print(f"currentStep:{current_step}")
                # 确保 current_step 为有效的整数索引
                if isinstance(current_step, int) and 0 <= current_step <= len(step_list):
                    md_lines.append(f"## Step {current_step+1}: {step_list[current_step]}")
                else:
                    md_lines.append("## Step: Unknown")
            
            elif log_type == 'solution/panel/update':
                solution = detail_info.get("solution")
                md_lines.append(solution+'\n')


            elif log_type == "process/start_plan":
                if process_start_time is None and current_time is not None:
                    process_start_time = current_time

            elif log_type == "config/info":
                agents = detail_info.get("agent_list", [])
                for agent in agents:
                    name = agent.get("name")
                    if name:
                        agent_list.append(name)
                        if name not in agent_conv_counts:
                            agent_conv_counts[name] = 0

                steps = detail_info.get("step_list",[])
                for step in steps:
                    name = step.get('name')
                    if name:
                        step_list.append(name)

    if process_start_time and last_time:
        time_diff = last_time - process_start_time
        time_diff_str = str(time_diff)
    else:
        time_diff_str = "N/A"

    filtered_agent_counts = {agent: agent_conv_counts.get(agent, 0) for agent in agent_list}

    md_lines.append(f"# Overview")
    md_lines.append(f"- GroupType: {group_type}")
    md_lines.append(f"- TimeUse: {time_diff_str}")
    md_lines.append(f"- ChatCnt: {user_talk_count}")
    md_lines.append(f"- ChatTotalLength: {total_content_length}")
    md_lines.append("## Roles")
    if filtered_agent_counts:
        for agent, count in filtered_agent_counts.items():
            md_lines.append(f"- {agent} {count}")
    else:
        md_lines.append("No agent information found.")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    print(f"Processed {tsv_path} -> {md_path}")


def main():
    history_dir = "history"
    formatted_dir = "formatted"
    
    # 若 formatted 文件夹不存在则创建
    if not os.path.exists(formatted_dir):
        os.makedirs(formatted_dir)
    
    # 定义文件名中组别代码到真实类型的映射
    type_map = {
        "A": "MultiVR",
        "B": "MultiWeb",
        "C": "SingleVR"
    }
    
    # 遍历 history 文件夹下所有 tsv 文件，文件名格式为 mm-dd@hh:mm-type.tsv
    for filename in os.listdir(history_dir):
        if filename.endswith(".tsv"):
            tsv_path = os.path.join(history_dir, filename)
            base_name = os.path.splitext(filename)[0]  # e.g. "03-06@15:50-B"
            # 按'-'拆分，提取最后部分作为组别代码
            parts = base_name.rsplit('-', 1)
            if len(parts) == 2:
                time_part, group_code = parts
                group_type = type_map.get(group_code, "Unknown")
            else:
                group_type = "Unknown"
            
            md_filename = base_name + ".md"
            md_path = os.path.join(formatted_dir, md_filename)
            # 如果同名的 markdown 文件已存在，则跳过
            if os.path.exists(md_path):
                print(f"Skipping {filename}, formatted file already exists.")
                continue
            # 传递额外的group_type参数
            process_file(tsv_path, md_path, group_type)


if __name__ == "__main__":
    main()
