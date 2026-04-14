import math
from collections import defaultdict

import numpy as np

from .models import InteractionEvent

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except Exception:
    torch = None
    nn = None
    F = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

RAG_VECTOR_DIM = 128
_ST_MODEL = None


def _compress_vector(vec, target_dim=RAG_VECTOR_DIM):
    arr = np.asarray(vec, dtype=np.float32)
    if arr.size == target_dim:
        return arr.tolist()

    if arr.size < target_dim:
        padded = np.zeros(target_dim, dtype=np.float32)
        padded[: arr.size] = arr
        arr = padded
    else:
        chunks = np.array_split(arr, target_dim)
        arr = np.array([chunk.mean() for chunk in chunks], dtype=np.float32)

    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()


def sentence_embedding(text):
    global _ST_MODEL
    if SentenceTransformer is None:
        return _compress_vector([hash(token) % 997 / 997.0 for token in text.split()][:RAG_VECTOR_DIM])

    if _ST_MODEL is None:
        _ST_MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    emb = _ST_MODEL.encode([text], normalize_embeddings=True)[0]
    return _compress_vector(emb, target_dim=RAG_VECTOR_DIM)


def _event_item_key(event):
    return f"{event.product_service}:{event.product_id}"


def build_customer_sequences(min_len=2):
    events = InteractionEvent.objects.filter(product_id__isnull=False).order_by('customer_id', 'occurred_at')
    by_customer = defaultdict(list)
    for event in events.iterator(chunk_size=4000):
        by_customer[event.customer_id].append(_event_item_key(event))

    sequences = []
    for _, seq in by_customer.items():
        if len(seq) >= min_len:
            sequences.append(seq)
    return sequences


def _build_vocab(sequences):
    vocab = {'<pad>': 0}
    for seq in sequences:
        for token in seq:
            if token not in vocab:
                vocab[token] = len(vocab)
    rev = {v: k for k, v in vocab.items()}
    return vocab, rev


if nn is not None:
    class GRU4RecModel(nn.Module):
        def __init__(self, vocab_size, emb_dim=64, hidden_dim=128):
            super().__init__()
            self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
            self.gru = nn.GRU(emb_dim, hidden_dim, batch_first=True)
            self.fc = nn.Linear(hidden_dim, vocab_size)

        def forward(self, x):
            h = self.emb(x)
            out, _ = self.gru(h)
            logits = self.fc(out[:, -1, :])
            return logits


    class TransformerNextItem(nn.Module):
        def __init__(self, vocab_size, emb_dim=96, nhead=4, layers=2, max_len=20):
            super().__init__()
            self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
            self.pos = nn.Embedding(max_len, emb_dim)
            encoder_layer = nn.TransformerEncoderLayer(d_model=emb_dim, nhead=nhead, batch_first=True)
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=layers)
            self.fc = nn.Linear(emb_dim, vocab_size)
            self.max_len = max_len

        def forward(self, x):
            pos_idx = torch.arange(x.size(1), device=x.device).unsqueeze(0).expand(x.size(0), -1)
            h = self.emb(x) + self.pos(pos_idx)
            out = self.encoder(h)
            logits = self.fc(out[:, -1, :])
            return logits


def _prepare_training_pairs(sequences, vocab, window=5):
    xs, ys = [], []
    for seq in sequences:
        ids = [vocab[token] for token in seq]
        for idx in range(1, len(ids)):
            start = max(0, idx - window)
            prefix = ids[start:idx]
            xs.append(prefix)
            ys.append(ids[idx])

    max_len = max((len(x) for x in xs), default=1)
    padded = []
    for x in xs:
        pad = [0] * (max_len - len(x))
        padded.append(pad + x)
    return np.array(padded, dtype=np.int64), np.array(ys, dtype=np.int64), max_len


def _train_sequence_model(model, X, y, epochs=3, lr=1e-3):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    X_tensor = torch.tensor(X, dtype=torch.long, device=device)
    y_tensor = torch.tensor(y, dtype=torch.long, device=device)

    for _ in range(max(1, epochs)):
        model.train()
        logits = model(X_tensor)
        loss = F.cross_entropy(logits, y_tensor)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        logits = model(X_tensor)
        pred = logits.argmax(dim=1)
        acc = (pred == y_tensor).float().mean().item()
    return model, {'train_accuracy': round(float(acc), 4), 'samples': int(len(y))}


def _build_next_lookup(model, vocab, rev, top_k=20):
    lookup = {}
    device = next(model.parameters()).device
    for token, token_id in vocab.items():
        if token_id == 0:
            continue
        x = torch.tensor([[token_id]], dtype=torch.long, device=device)
        with torch.no_grad():
            logits = model(x)
            top_ids = torch.topk(logits[0], k=min(top_k, logits.shape[-1])).indices.tolist()
        candidates = [rev[i] for i in top_ids if i in rev and i != 0 and rev[i] != token]
        lookup[token] = candidates[:top_k]
    return lookup


def train_gru4rec_model(epochs=3):
    if torch is None:
        return None

    sequences = build_customer_sequences(min_len=2)
    if not sequences:
        return {'state': {'model_type': 'gru4rec', 'next_lookup': {}}, 'metrics': {'samples': 0}}

    vocab, rev = _build_vocab(sequences)
    X, y, _ = _prepare_training_pairs(sequences, vocab, window=6)
    if len(y) == 0:
        return {'state': {'model_type': 'gru4rec', 'next_lookup': {}}, 'metrics': {'samples': 0}}

    model = GRU4RecModel(vocab_size=len(vocab), emb_dim=64, hidden_dim=128)
    model, metrics = _train_sequence_model(model, X, y, epochs=epochs)
    lookup = _build_next_lookup(model, vocab, rev)

    state = {
        'model_type': 'gru4rec',
        'next_lookup': lookup,
    }
    return {'state': state, 'metrics': metrics}


def train_transformer_model(epochs=3):
    if torch is None:
        return None

    sequences = build_customer_sequences(min_len=2)
    if not sequences:
        return {'state': {'model_type': 'transformer', 'next_lookup': {}}, 'metrics': {'samples': 0}}

    vocab, rev = _build_vocab(sequences)
    X, y, max_len = _prepare_training_pairs(sequences, vocab, window=10)
    if len(y) == 0:
        return {'state': {'model_type': 'transformer', 'next_lookup': {}}, 'metrics': {'samples': 0}}

    model = TransformerNextItem(vocab_size=len(vocab), emb_dim=96, nhead=4, layers=2, max_len=max(10, max_len))
    model, metrics = _train_sequence_model(model, X, y, epochs=epochs)
    lookup = _build_next_lookup(model, vocab, rev)

    state = {
        'model_type': 'transformer',
        'next_lookup': lookup,
    }
    return {'state': state, 'metrics': metrics}


def train_gnn_recommender(epochs=50, emb_dim=64):
    if torch is None:
        return None

    events = InteractionEvent.objects.filter(product_id__isnull=False).order_by('occurred_at')
    user_map = {}
    item_map = {}
    interactions = []

    for event in events.iterator(chunk_size=5000):
        u = event.customer_id
        it = _event_item_key(event)
        if u not in user_map:
            user_map[u] = len(user_map)
        if it not in item_map:
            item_map[it] = len(item_map)
        interactions.append((user_map[u], item_map[it]))

    if not interactions:
        return {'state': {'model_type': 'gnn', 'user_topk': {}}, 'metrics': {'samples': 0}}

    n_users = len(user_map)
    n_items = len(item_map)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    user_emb = nn.Embedding(n_users, emb_dim).to(device)
    item_emb = nn.Embedding(n_items, emb_dim).to(device)
    optimizer = torch.optim.Adam(list(user_emb.parameters()) + list(item_emb.parameters()), lr=3e-3)

    edge_u = torch.tensor([u for u, _ in interactions], dtype=torch.long, device=device)
    edge_i = torch.tensor([i for _, i in interactions], dtype=torch.long, device=device)

    def propagate(u_emb, i_emb):
        agg_u = torch.zeros_like(u_emb)
        agg_i = torch.zeros_like(i_emb)
        agg_u.index_add_(0, edge_u, i_emb[edge_i])
        agg_i.index_add_(0, edge_i, u_emb[edge_u])
        deg_u = torch.bincount(edge_u, minlength=n_users).float().unsqueeze(-1).to(device).clamp_min(1.0)
        deg_i = torch.bincount(edge_i, minlength=n_items).float().unsqueeze(-1).to(device).clamp_min(1.0)
        return agg_u / deg_u, agg_i / deg_i

    for _ in range(max(1, epochs)):
        u0 = user_emb.weight
        i0 = item_emb.weight
        u1, i1 = propagate(u0, i0)
        u2, i2 = propagate(u1, i1)
        uf = (u0 + u1 + u2) / 3.0
        itf = (i0 + i1 + i2) / 3.0

        pos_scores = (uf[edge_u] * itf[edge_i]).sum(dim=1)
        neg_i = torch.randint(0, n_items, size=edge_i.shape, device=device)
        neg_scores = (uf[edge_u] * itf[neg_i]).sum(dim=1)
        loss = -torch.log(torch.sigmoid(pos_scores - neg_scores) + 1e-8).mean()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        u0 = user_emb.weight
        i0 = item_emb.weight
        u1, i1 = propagate(u0, i0)
        u2, i2 = propagate(u1, i1)
        uf = (u0 + u1 + u2) / 3.0
        itf = (i0 + i1 + i2) / 3.0
        scores = uf @ itf.T

    rev_user = {idx: user for user, idx in user_map.items()}
    rev_item = {idx: item for item, idx in item_map.items()}

    user_topk = {}
    top_k = min(30, n_items)
    for u_idx in range(n_users):
        top_idx = torch.topk(scores[u_idx], k=top_k).indices.tolist()
        recs = [rev_item[i] for i in top_idx]
        user_topk[str(rev_user[u_idx])] = recs

    state = {
        'model_type': 'gnn',
        'user_topk': user_topk,
    }
    return {
        'state': state,
        'metrics': {
            'samples': len(interactions),
            'users': n_users,
            'items': n_items,
        },
    }


def infer_next_items_from_snapshot(snapshot_state, source_item_key, limit=5):
    lookup = snapshot_state.get('next_lookup', {})
    candidates = lookup.get(source_item_key, [])[:limit]
    output = []
    for key in candidates:
        service, pid = key.split(':', 1)
        output.append({'product_service': service, 'product_id': int(pid), 'count': 1})
    return output


def infer_gnn_recommendations(snapshot_state, customer_id, limit=10):
    topk = snapshot_state.get('user_topk', {})
    keys = topk.get(str(customer_id), [])[:limit]
    output = []
    for rank, key in enumerate(keys):
        service, pid = key.split(':', 1)
        output.append(
            {
                'product_service': service,
                'product_id': int(pid),
                'score': round(1.0 / (rank + 1), 4),
                'reason': ['gnn_graph'],
            }
        )
    return output
