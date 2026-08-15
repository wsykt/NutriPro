import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector.retriever import retriever

PDF_FILE = r"C:\Users\13425\Desktop\个人健康助手\预包装食品蛋白质质量标示规范（TCNSS+046-2026）.pdf"


def extract_text_from_pdf(pdf_path):
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except ImportError:
        print("PyPDF2 未安装，尝试使用其他方式...")
        return None
    except Exception as e:
        print(f"读取PDF失败: {e}")
        return None


def clean_text(text):
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\u4e00-\u9fff0-9a-zA-Z，。！？、；：""''（）【】《》—…·]', '', text)
    return text.strip()


def split_into_chunks(text, chunk_size=500):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            last_period = text.rfind('。', start, end)
            last_comma = text.rfind('，', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1
            elif last_comma > start + chunk_size // 2:
                end = last_comma + 1
        chunks.append(text[start:end].strip())
        start = end
    return chunks


def main():
    print("=" * 60)
    print("导入PDF到向量知识库")
    print("=" * 60)
    
    if not os.path.exists(PDF_FILE):
        print(f"错误: PDF文件不存在 - {PDF_FILE}")
        return
    
    print(f"\n读取PDF文件: {PDF_FILE}")
    
    text = extract_text_from_pdf(PDF_FILE)
    
    if not text:
        print("无法提取PDF内容，尝试使用pdftotext...")
        try:
            import subprocess
            result = subprocess.run(['pdftotext', PDF_FILE, '-'], capture_output=True, text=True, encoding='utf-8')
            text = result.stdout
        except Exception as e:
            print(f"pdftotext也失败: {e}")
            return
    
    if not text or len(text) < 100:
        print("提取的文本内容过少，可能是扫描版PDF")
        return
    
    print(f"提取到文本长度: {len(text)} 字符")
    
    clean = clean_text(text)
    print(f"清理后文本长度: {len(clean)} 字符")
    
    chunks = split_into_chunks(clean, chunk_size=500)
    print(f"分割为 {len(chunks)} 个片段")
    
    documents = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        if len(chunk) < 50:
            continue
        documents.append(chunk)
        metadatas.append({
            "category": "nutrition_standard",
            "source": "预包装食品蛋白质质量标示规范（TCNSS+046-2026）",
            "chunk_index": i,
        })
        ids.append(f"pdf_protein_standard_{i}")
    
    print(f"准备添加 {len(documents)} 条到向量库")
    
    batch_size = 100
    total_batches = (len(documents) + batch_size - 1) // batch_size
    success_count = 0
    
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        try:
            retriever.add(batch_docs, batch_metas, batch_ids)
            success_count += len(batch_docs)
            print(f"已添加批次 {i//batch_size + 1}/{total_batches}, 累计 {success_count} 条")
        except Exception as e:
            print(f"添加批次失败: {e}")
            return
    
    print(f"\n向量知识库更新完成，总记录数: {retriever.count()}")
    
    print("\n测试搜索:")
    results = retriever.search("蛋白质质量标示", top_k=3)
    for j, r in enumerate(results):
        print(f"{j+1}. 相似度: {r['similarity']:.4f}, 内容: {r['content'][:100]}...")
    
    print("\n" + "=" * 60)
    print("PDF导入完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()