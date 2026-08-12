# -*- coding: utf-8 -*-
"""项目8第3步：解析 one_article.xml 的标题、作者和摘要。"""

import xml.etree.ElementTree as ET


def get_all_text(node):
    """取得一个 XML 标签内部的全部文字。"""
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


# 读取第2步保存的 XML 文件。
tree = ET.parse("one_article.xml")
root = tree.getroot()

# .// 表示不管中间隔了多少层，都向下寻找这个标签。
pmid_node = root.find(".//PMID")
title_node = root.find(".//ArticleTitle")

pmid = get_all_text(pmid_node)
title = get_all_text(title_node)

# findall() 会返回所有匹配的作者节点。
authors = []
for author_node in root.findall(".//AuthorList/Author"):
    last_name = get_all_text(author_node.find("LastName"))
    initials = get_all_text(author_node.find("Initials"))
    collective_name = get_all_text(author_node.find("CollectiveName"))

    if collective_name:
        authors.append(collective_name)
    elif last_name:
        authors.append(last_name + " " + initials)

# 一篇摘要可能有 BACKGROUND、METHODS、RESULTS 等多个段落。
abstract_parts = []
for abstract_node in root.findall(".//Abstract/AbstractText"):
    label = abstract_node.attrib.get("Label", "")
    text = get_all_text(abstract_node)
    if label:
        abstract_parts.append(label + ": " + text)
    else:
        abstract_parts.append(text)

abstract = "\n".join(abstract_parts)

print("PMID：", pmid)
print("标题：", title)
print("作者：", " | ".join(authors))
print("摘要：")
print(abstract if abstract else "这篇文献没有公开摘要")
