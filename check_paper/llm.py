import os
from langchain_openai import ChatOpenAI
from pymilvus import Collection

import milvus_test

def get_correction_suggestion(content,api_url):
    api_key = "sk-IwmKcBKY42zk7gqsE3B502F9699d476b808e573fE4A74206"
    # 设置环境变量
    os.environ["OPENAI_API_KEY"] = api_key
    chat = ChatOpenAI(model="qwen-turbo", openai_api_base=api_url)

    examples = milvus_test.search_vector(content)

    prompt = f"""
        任务：扮演一名专业的律师，秉持严谨、认真负责的态度审查合同的部分内容，针对合同中表述不清楚、不严谨或不符合法律规定之处，给出具体的修改建议。
        这里有一些简单的例子：
        
        示例：{examples}
        
        请你学习上面示例中的修改习惯和表达风格审查下面的内容并返回修改批注：
        {content}
        ###
        强调！！！最终的输出结果为修改建议（这部分包括修改理由。）和修改后的内容。不要添加额外的输出,使用下面的格式。：
        修改建议：
        修改后的内容：
    """
    response = chat.invoke(prompt)
    print(response.content)
    return response.content

if __name__ == '__main__':
    get_correction_suggestion("ashdf","https://api.rcouyi.com/v1")
