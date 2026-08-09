import os
from config.settings import settings

model_path = settings.EMBEDDING_MODEL_NAME
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

from sentence_transformers import SentenceTransformer


class BGEEmbedder:

    def __init__(self):
        self.model = SentenceTransformer(
            model_path,
            local_files_only=True,
            trust_remote_code=False
        )

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        texts = [f"为这个句子生成向量以用于检索: {t}" for t in texts]
        emb = self.model.encode(texts, normalize_embeddings=True)
        return emb

    def encode_query(self, text):
        return self.encode(text)[0]


embedder = BGEEmbedder()