import json
import time

import numpy as np
from tqdm import tqdm
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from openai import OpenAI
import os
from sentence_transformers import SentenceTransformer
# 使用新的 Hugging Face 模型
# new_model = SentenceTransformer('sentence-transformer/paraphrase-MiniLM-L6-v2')
# 全局配置
MILVUS_HOST = '10.220.138.111'  # Milvus 服务器的主机地址
MILVUS_PORT = '19530'  # Milvus 服务器的端口号
DB_NAME = 'BS_contract_review'  # 数据库名称
COLLECTION_NAME = 'contract_review'  # 集合名称
ENGINE = "text-embedding-3-small"  # Milvus 使用的引擎
EMBEDDING_DIMENSIONS = 768  # 文本向量的维度
BATCH_SIZE = 15  # 批量处理的文本数量
API_SECRET_KEY = "sk-YXXtQVrIHMmEeHT4148a98D03cEf404392E546C482962978"  # OpenAI API 的密钥
BASE_URL = "https://api.rcouyi.com/v1"  # OpenAI API 的基本 URL

# 标志变量，用于检查 Milvus 是否已经初始化
milvus_initialized = False


# 连接 Milvus 数据库
# def connect_to_milvus():
#     connections.connect(alias='default', host=MILVUS_HOST, port=MILVUS_PORT, db_name=DB_NAME)

MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 5  # 重试延迟时间（秒）

# 连接 Milvus 数据库
def connect_to_milvus():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            connections.connect(alias='default', host=MILVUS_HOST, port=MILVUS_PORT, db_name=DB_NAME)
            # print("Milvus 连接成功！")
            return True
        except Exception as e:
            print(f"Milvus 连接失败：{e}")
            print(f"重试中... (尝试次数: {retries + 1}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
            retries += 1
    print("达到最大重试次数，连接 Milvus 失败！")
    return False

# 创建 Milvus 集合
def create_collection():
    # 定义字段模式
    field1 = FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True)
    field2 = FieldSchema(name="original_text", dtype=DataType.VARCHAR, max_length=65535)
    field3 = FieldSchema(name="modified_text", dtype=DataType.VARCHAR, max_length=65535)
    field4 = FieldSchema(name="text_vector", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIMENSIONS)
    field5 = FieldSchema(name="previous_text", dtype=DataType.VARCHAR, max_length=65535)
    field6 = FieldSchema(name="subsequent_text", dtype=DataType.VARCHAR, max_length=65535)
    schema = CollectionSchema(fields=[field1, field2, field3, field4, field5, field6])

    # 删除已存在的同名集合，然后创建新集合
    res = utility.drop_collection(collection_name=COLLECTION_NAME)
    collection = Collection(name=COLLECTION_NAME, schema=schema, using='default')

    # 创建向量索引
    index_params = {"index_type": "AUTOINDEX", "metric_type": "L2", "params": {}}
    collection.create_index(field_name="text_vector", index_params=index_params, index_name='vector_idx')
    collection.load()
    return collection


# 从 JSON 文件中读取文本数据
def get_text(file_path):
    with open(file_path, 'r', encoding="utf-8") as json_file:
        data = json.load(json_file)
    return data


# 使用 OpenAI API 对文本进行批量嵌入
def batch_embeddings(docs):
    client = OpenAI(api_key=API_SECRET_KEY, base_url=BASE_URL)
    embedding = client.embeddings.create(
        model=ENGINE,
        input=docs,
        dimensions=EMBEDDING_DIMENSIONS,
    ).data
    return [d.embedding for d in embedding]


# 将数据插入到 Milvus 集合中
def insert_data(collection, data):
    collection.insert(data=data)


# 更新数据到 Zilliz Milvus
def update_article_zilliz():
    global milvus_initialized  # 使用全局变量

    count = 0
    data_list = []
    docs_embeddings = []

    # 检查 Milvus 是否已经初始化，如果未初始化，则执行初始化操作
    if not milvus_initialized:
        connect_to_milvus()  # 先连接到 Milvus 数据库
        collection = create_collection()  # 创建 Milvus 集合
        milvus_initialized = True  # 将标志变量设置为 True，表示 Milvus 已经初始化
    else:
        collection = Collection(COLLECTION_NAME)  # 如果 Milvus 已经初始化，则直接获取集合对象

    chunks = get_text("alljson.json")
    for chunk in tqdm(chunks):
        original_text = chunk.get("原文", "")
        if not original_text:
            continue

        count += 1
        docs_embeddings.append(original_text)
        data_list.append({
            "original_text": original_text,
            "modified_text": chunk.get("修改后", ""),
            "previous_text": chunk["上下文"]["前文"],
            "subsequent_text": chunk["上下文"]["后文"],
        })

        if len(docs_embeddings) >= BATCH_SIZE:
            embeddings = batch_embeddings(docs_embeddings)

            for i, embedding in enumerate(embeddings):
                data_list[i]["text_vector"] = embedding

            insert_data(collection, data_list)

            docs_embeddings = []
            data_list = []

    if docs_embeddings:
        embeddings = batch_embeddings(docs_embeddings)

        for i, embedding in enumerate(embeddings):
            data_list[i]["text_vector"] = embedding

        insert_data(collection, data_list)

    print(f"文档嵌入完成，共插入{count}条数据")

    milvus_initialized = True  # 将标志变量设置为 True，表示 Milvus 已经初始化



# 使用 Milvus 进行向量搜索
# 更新搜索函数以使用新的模型
def search_vector(data_match):
    connect_to_milvus()
    collection = Collection(COLLECTION_NAME)
    collection.load()

    # # 使用新的模型生成嵌入
    # new_embedding = new_model.encode(data_match, convert_to_numpy=True)
    client = OpenAI(api_key=API_SECRET_KEY, base_url=BASE_URL)
    data_embedding = client.embeddings.create(
        model=ENGINE,
        input=data_match,
        dimensions=EMBEDDING_DIMENSIONS,
    ).data

    # # 确保新嵌入的维度为 768，通过填充或者其他方法
    # if new_embedding.shape[0] < EMBEDDING_DIMENSIONS:
    #     padded_embedding = np.pad(new_embedding, (0, EMBEDDING_DIMENSIONS - new_embedding.shape[0]), 'constant')
    # elif new_embedding.shape[0] > EMBEDDING_DIMENSIONS:
    #     padded_embedding = new_embedding[:EMBEDDING_DIMENSIONS]
    # else:
    #     padded_embedding = new_embedding

    search_params = {"metric_type": "L2", "params": {"nprobe": 10}, "offset": 0}
    results = collection.search(
        data=[data_embedding[0].embedding],
        anns_field="text_vector",
        param=search_params,
        limit=1,
        output_fields=['original_text', 'modified_text', "previous_text", "subsequent_text"],
        consistency_level="Strong"
    )

    collection.release()
    response_all = []
    if results and results[0]:
        for result in results[0]:
            dic = {"original_text": result.entity.get('original_text'), "modified_text": result.entity.get('modified_text')}
            response_all.append(dic)
        print("匹配结果：", response_all)
    else:
        print("未找到匹配结果或其他异常发生，返回默认内容：")
        data_match1 = "乙方认为甲方代表的指令不合理，应在收到指令后24小时内向甲方代表提出修改指令的书面报告，甲方代表可作出修改指令或继续执行原指令的决定。紧急情况下，甲方代表要求乙方立即执行的指令，乙方应无条件予以执行，乙方拒不执行指令的，甲方有权解除本合同。"
        data_match2 = "3.2.5 乙方认为甲方代表的指令不合理，应在收到指令后24小时内向甲方代表提出修改指令的书面报告，甲方代表可作出修改指令或继续执行原指令的决定。紧急情况下，甲方代表要求乙方立即执行的指令，乙方应无条件予以执行，乙方拒不执行指令的，甲方有权解除本合同。"

        response_all.append({"original_text": data_match1, "modified_text": data_match2})

    return response_all

# 读取文件内容
def read_file(path):
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content
