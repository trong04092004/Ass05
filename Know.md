# Know

## 1) Su dung model gi?
He thong chatbot/AI trong project nay la mo hinh hybrid, khong phai 1 LLM duy nhat:

- RAG retriever: dung sentence embedding tu Sentence-Transformers (model `all-MiniLM-L6-v2`) de tim tai lieu lien quan.
- Behavior recommendation model: co cac model train duoc (`markov`, `gru4rec`, `transformer`, `gnn`) va co co che active model/fallback.
- Chat answer generation: hien tai tao cau tra loi theo intent + tai lieu retrieve + template/rule (khong sinh van ban bang OpenAI/Gemini).

Tom lai: AI o day la RAG + recommendation + rule-based response orchestration.

## 2) Lay API LLM hay tu train?
Hien trang code:

- Khong thay goi API LLM ben ngoai (khong co OpenAI/Gemini/Claude endpoint call trong flow chat).
- Co train model noi bo cho recommendation/next-item (`gru4rec`, `transformer`, `gnn`, fallback `markov`).
- Embedding cho RAG dung Sentence-Transformers local trong service (neu chua co model se download 1 lan, sau do chay local).

=> Tra loi ngan gon: khong goi LLM API cho chat generation; recommendation thi tu train trong he thong.

## 3) Flow chatbot nhu nao?
Flow tong quan:

1. Frontend goi `POST /api/ai/chat/` vao API Gateway.
2. Gateway bo sung `customer_id` tu session (neu co), sau do goi AI service `POST /api/ai/chat/`.
3. AI service:
   - Kiem tra guardrail (block jailbreak/prompt injection term).
   - Detect intent (doi tra, giao hang, thanh toan, goi y, general).
   - Retrieve RAG documents (`top_k`).
   - Neu co `customer_id` thi lay personalized recommendations + next products.
   - Tao answer theo template + context.
4. Gateway nhan payload, enrich recommendation thanh san pham co that (name/price/image/link), loc theo query va service neu can.
5. Neu recommendation rong, Gateway fallback sang endpoint recommend hoac keyword search/catalog fallback.
6. Gateway tra ve frontend: `answer`, `retrieved_documents`, `personalized_recommendations`, ...

## 4) RAG nhu nao?
RAG pipeline hien tai:

- Nguon tri thuc: bang `RAGDocument` (title/content/doc_type/embedding).
- Index:
  - Khi tao/sua RAGDocument: tinh embedding.
  - Co endpoint reindex: `POST /api/ai/reindex-rag/`.
- Retrieval:
  - Neu ho tro pgvector thi retrieve theo cosine distance tren embedding.
  - Neu khong thi fallback lexical scoring (token overlap).
- Generation:
  - Chon top docs, lay snippet, dua vao answer template theo intent.
  - Khong dung LLM external de sinh tu do; hien tai la concise/rule-driven response.

## Ket luan nhanh cho 4 cau hoi
- Model gi: hybrid (Sentence-Transformers + behavior models + rule/template chat).
- API LLM hay tu train: khong goi LLM API de chat; recommendation co tu train.
- Flow chatbot: Frontend -> Gateway -> AI service (intent + retrieval + rec) -> Gateway enrich/fallback -> Frontend.
- RAG: embedding + vector/lexical retrieval tren `RAGDocument`, sau do render answer theo intent.
