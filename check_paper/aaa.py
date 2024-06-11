from spire.doc import *


def revise_document(revise_filepath, processed_filepath, contract_comments):
    doc = Document()
    doc.LoadFromFile(processed_filepath)
    for item in contract_comments:
        doc = replace_text(doc, item['text'], item['comment1'])
    # 保存文档
    doc.SaveToFile(revise_filepath)
    doc.Close()


def replace_text(document, old_text, new_text):
    # 将替换模式更改为替换第一个匹配项
    document.ReplaceFirst = True
    try:
        # 将第一个出现的文本替换为另一个文本
        document.Replace(old_text,
                         new_text,
                         False, True)
        return document
    except Exception as e:
        print('替换文本出错')
        return document