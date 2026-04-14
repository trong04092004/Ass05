AI Service - Knowledge Graph + Behavior Learning + RAG Chat

Muc tieu
- Xay dung AI service cap production cho he thong thuong mai dien tu microservice Django.
- Hop nhat 3 lop thong minh:
  1) Knowledge Graph (ngu canh va quan he)
  2) Behavior Model (du doan hanh vi tiep theo)
  3) RAG Chat (hoi dap co truy xuat tri thuc)

Kien truc
- interaction-events: ingest hanh vi tu cac service (view, click, search, cart, purchase, chat)
- graph/nodes + graph/edges: kho tri thuc dang do thi semantic
- behavior-models: snapshot mo hinh Markov cho du doan chuoi hanh vi
- rag-documents: kho tai lieu tri thuc cho chat retrieval
- ai endpoints: orchestration build graph, train model, recommend, chat
- gateway integration: goi realtime recommendation tren product detail va cart/checkout page

Config production
- GRAPH_BACKEND=neo4j|django
- NEO4J_URI=bolt://neo4j:7687
- NEO4J_USER=neo4j
- NEO4J_PASSWORD=your_password
- CELERY_BROKER_URL=redis://redis:6379/0
- CELERY_RESULT_BACKEND=redis://redis:6379/0

Cong thuc trong so do thi
- Edge tu user den product duoc cong don theo su kien:
  w(u,p) = alpha*click + beta*cart + gamma*purchase + delta*view + epsilon*search
- Gia tri mac dinh trong source:
  view=0.4, click=1.0, search=0.3, cart=2.5, purchase=5.0, chat=0.2

API Chinh
- POST /api/interaction-events/
  ingest event va cap nhat graph ngay lap tuc

- POST /api/ai/build-graph/
  body: {"full_rebuild": true|false, "customer_id": optional}

- POST /api/ai/train-behavior/
  body: {"model_type": "gru4rec|transformer|gnn|markov", "min_transitions": 1, "epochs": 3}

- POST /api/ai/recommend/
  body: {"customer_id": 1001, "limit": 10}

- POST /api/ai/chat/
  body: {"customer_id": 1001, "message": "goi y sach", "top_k": 5}

- POST /api/ai/reindex-rag/
  tai tao vector embedding cho toan bo RAGDocument

- POST /api/ai/sync-neo4j/
  body: {"full_rebuild": true|false, "customer_id": optional}

- POST /api/ai/retrain-auto-switch/
  body: {"models": ["gru4rec","transformer","gnn"], "min_transitions": 1, "epochs": 3}

- POST /api/ai/auto-switch/
  chon model behavior tot nhat tu cac snapshot theo metric

- GET /api/ai/active-model/
  lay model behavior dang active de phuc vu inference

Van hanh voi Docker Compose
1) Da duoc noi vao docker-compose voi service name ai-service, host port 18009.
2) Da tao DB bookstore_micro_recommender trong init_db.sql.
3) Khoi dong:
   docker compose up --build -d ai-service

Swagger
- http://localhost:18009/api/docs/

Mo rong production khuyen nghi
- Graph DB:
  chuyen KnowledgeNode/KnowledgeEdge sang Neo4j (Cypher) hoac Neptune khi quy mo lon.
- Deep Learning:
  da ho tro train GRU4Rec, Transformer, GNN thong qua endpoint train-behavior.
- RAG:
  retriever embedding dung Sentence-Transformers, luu vector trong pgvector + cosine distance.
- Event-driven:
  ingest InteractionEvent qua broker (Kafka/RabbitMQ), xu ly bat dong bo theo stream.

Script sync Neo4j tu InteractionEvent
- python manage.py sync_neo4j_graph --full-rebuild
- python manage.py sync_neo4j_graph --customer-id 1001

Lich retrain dinh ky
- Celery Beat:
  - retrain 30 phut/lần
  - auto-switch 10 phut/lần
  - reindex RAG luc 02:00 hang ngay

- Cron command (fallback neu khong dung celery):
  python manage.py retrain_models --models gru4rec transformer gnn --epochs 3

Train Deep Learning nhanh
- POST /api/ai/train-behavior/ {"model_type":"gru4rec","epochs":5}
- POST /api/ai/train-behavior/ {"model_type":"transformer","epochs":5}
- POST /api/ai/train-behavior/ {"model_type":"gnn","epochs":8}
