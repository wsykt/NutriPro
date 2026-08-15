import os
import sys
import json
from PyPDF2 import PdfReader

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vector.retriever import retriever


def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
    except Exception as e:
        print(f"提取 PDF 失败 {pdf_path}: {e}")
    return text


def split_text(text, chunk_size=500, overlap=50):
    chunks = []
    text = text.replace('\n', ' ').replace('  ', ' ')
    text = ' '.join(text.split())
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
        if start >= len(text):
            break
    return chunks


def process_pdfs(pdf_dir):
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    print(f"发现 {len(pdf_files)} 个 PDF 文件")

    all_documents = []
    all_metadatas = []
    all_ids = []

    for i, pdf_file in enumerate(pdf_files):
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print(f"处理 {i+1}/{len(pdf_files)}: {pdf_file}")
        
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            print(f"  跳过：未提取到文本")
            continue
        
        chunks = split_text(text)
        print(f"  生成 {len(chunks)} 个文本块")
        
        for j, chunk in enumerate(chunks):
            if len(chunk) < 50:
                continue
            
            doc_id = f"pdf_{i}_{j}"
            all_documents.append(chunk)
            all_metadatas.append({
                "source": pdf_file,
                "category": "pdf_document",
                "chunk_index": j,
                "total_chunks": len(chunks)
            })
            all_ids.append(doc_id)

    print(f"\n总共生成 {len(all_documents)} 个文档")
    return all_documents, all_metadatas, all_ids


def main():
    pdf_dir = os.path.join(os.path.dirname(__file__), '..', 'knowledge', 'pdfs')
    
    if not os.path.exists(pdf_dir):
        print(f"PDF 目录不存在: {pdf_dir}")
        return

    documents, metadatas, ids = process_pdfs(pdf_dir)
    
    if not documents:
        print("没有找到有效的文档")
        return

    print("\n正在清空旧知识库...")
    retriever.clear()
    
    print(f"正在插入 {len(documents)} 条记录到向量数据库...")
    retriever.add(documents, metadatas, ids)
    
    print(f"\n完成！向量数据库中共有 {retriever.count()} 条记录")


if __name__ == "__main__":
    main()