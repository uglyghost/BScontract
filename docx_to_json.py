import os
import json
from docx import Document
from lxml import etree
import zipfile
import xml.etree.ElementTree as ET
import comtypes.client


def extract_comments(doc_path):
    comments = {}
    with zipfile.ZipFile(doc_path, 'r') as docx:
        # 检查comments.xml文件是否存在
        if 'word/comments.xml' in docx.namelist():
            with docx.open('word/comments.xml') as comments_xml:
                tree = ET.parse(comments_xml)
                root = tree.getroot()
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            for comment in root.findall('.//w:comment', namespaces):
                comment_id = comment.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                comment_text = ''.join(t.text for t in comment.findall('.//w:t', namespaces) if t.text)
                comments[comment_id] = comment_text
        else:
            print("No comments found in", doc_path)
    return comments


def parse_docx(doc_path, output_filename, context_size=2):
    doc = Document(doc_path)
    xml_content = etree.fromstring(doc._element.xml)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    comments = extract_comments(doc_path)
    output_data = []
    paragraphs = list(doc.paragraphs)
    for i, para in enumerate(paragraphs):
        para_xml = etree.fromstring(para._p.xml)
        original_text = para.text
        modified_text = ""
        comment_texts = []
        comment_refs = para_xml.xpath('.//w:commentRangeStart', namespaces=ns)
        for ref in comment_refs:
            comment_id = ref.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            if comment_id in comments:
                comment_texts.append(comments[comment_id])
        runs = para_xml.xpath('.//w:r', namespaces=ns)
        for run in runs:
            ins_texts = run.xpath('.//w:ins/w:t', namespaces=ns)
            if ins_texts:
                modified_text += ''.join([t.text for t in ins_texts if t.text is not None])
            normal_texts = run.xpath('.//w:t[not(parent::w:del)]', namespaces=ns)
            if normal_texts:
                modified_text += ''.join([t.text for t in normal_texts if t.text is not None])
        if original_text != modified_text or comment_texts:
            context = {
                "前文": ' '.join(p.text for p in paragraphs[max(0, i-context_size):i]),
                "后文": ' '.join(p.text for p in paragraphs[i+1:min(len(paragraphs), i+1+context_size)])
            }
            entry = {
                "原文": original_text,
                "修改后": modified_text,
                "批注": " | ".join(comment_texts),
                "上下文": context
            }
            output_data.append(entry)

    # 保存每个文件的输出数据到单独的JSON文件
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)


def doc_to_docx(doc_path):
    """将.doc文件转换为.docx（仅限Windows）"""
    word = comtypes.client.CreateObject('Word.Application')
    try:
        # 获取绝对路径并规范化
        abs_doc_path = os.path.abspath(doc_path)
        abs_doc_path = os.path.normpath(abs_doc_path)
        doc = word.Documents.Open(abs_doc_path)
        docx_path = os.path.splitext(abs_doc_path)[0] + '.docx'
        doc.SaveAs(docx_path, FileFormat=16)  # Word默认的.docx格式编号是16
        doc.Close()
        word.Quit()
        return docx_path
    except Exception as e:
        print(f"Error opening {abs_doc_path}: {e}")
        word.Quit()
        raise


def process_directory(directory_path, json_path):
    for filename in os.listdir(directory_path):
        doc_path = os.path.join(directory_path, filename)
        print(f"Processing: {doc_path}")  # 打印正在处理的文件路径
        # 移除原文件后缀，添加.json后缀
        output_filename = os.path.join(json_path, os.path.splitext(filename)[0] + '.json')
        if filename.endswith('.docx'):
            parse_docx(doc_path, output_filename)
        elif filename.endswith('.doc'):
            # 尝试转换.doc为.docx
            try:
                docx_path = doc_to_docx(doc_path)
                parse_docx(docx_path, output_filename)
                os.remove(docx_path)  # 转换后删除临时.docx文件
            except Exception as e:
                print(f"Failed to convert {doc_path}: {e}")


# 指定目录并调用处理函数
directory_path = './data/docx_files/'
json_path = './data/json_flies/'
process_directory(directory_path, json_path)
