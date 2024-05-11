import os
import json

def merge_json_files(directory_path, output_filename):
    # 所有合并数据的列表
    all_data = []

    # 遍历指定目录下的所有文件
    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            file_path = os.path.join(directory_path, filename)
            # 读取每个JSON文件
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                all_data.extend(data)  # 假设每个文件包含一个数据列表

    # 将合并后的数据写入一个新的JSON文件
    with open(output_filename, 'w', encoding='utf-8') as file:
        json.dump(all_data, file, ensure_ascii=False, indent=4)


# 使用示例
directory_path = './data/json_flies/'  # JSON文件的目录
output_filename = './output/alljson.json'  # 输出文件的路径
merge_json_files(directory_path, output_filename)
