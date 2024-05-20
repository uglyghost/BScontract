from spire.doc import *


def add_comment(doc, text, comment1):
    # 假设 get_correction_suggestion 和 add_comment 是已经定义好的函数

    # 查找要添加评论的文本
    try:
        # 尝试查找要添加评论的文本
        text = doc.FindString(text, True, True)
        if text is None:
            print('未找到文本')
            return doc
        # 如果找到了文本，可以在这里调用 add_comment 或其他函数
    except Exception as e:
        print('查找文本出错')
        return doc

    # 创建一个评论对象并设置评论的内容和作者
    comment = Comment(doc)
    comment.Body.AddParagraph().Text = comment1
    comment.Format.Author = "AI"

    # 将找到的文本作为文本范围，并获取其所属的段落
    range = text.GetAsOneRange()
    paragraph = range.OwnerParagraph

    # 将评论添加到段落中
    paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(range) + 1, comment)

    # 创建评论起始标记和结束标记，并将它们设置为创建的评论的起始标记和结束标记
    commentStart = CommentMark(doc, CommentMarkType.CommentStart)
    commentEnd = CommentMark(doc, CommentMarkType.CommentEnd)
    commentStart.CommentId = comment.Format.CommentId
    commentEnd.CommentId = comment.Format.CommentId

    # 在找到的文本之前和之后插入创建的评论起始和结束标记
    paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(range), commentStart)
    paragraph.ChildObjects.Insert(paragraph.ChildObjects.IndexOf(range) + 1, commentEnd)
    return doc


def add_comments(paper_comments, path1):
    doc = Document()
    doc.LoadFromFile(path1)
    for item in paper_comments:
        print(item)
        doc = add_comment(doc, item['text'], item['comment1'])

    # 保存文档
    doc.SaveToFile(path1)
    doc.Close()
