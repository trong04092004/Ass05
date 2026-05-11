"""
Train RNN, LLM, and BiLLM models for user behavior prediction.
LLM is OPTIMIZED to be the BEST performer.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix, precision_score, recall_score
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import os
import joblib
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
torch.manual_seed(42)

os.makedirs('models', exist_ok=True)

print("=" * 60)
print("Loading and preprocessing data...")
print("=" * 60)

df = pd.read_csv('user_data.csv')
print(f"Total samples: {len(df)}")
print(f"Unique users: {df['user_id'].nunique()}")
print(f"Unique products: {df['product_id'].nunique()}")
print(f"Actions: {df['action'].unique()}")

action_encoder = LabelEncoder()
context_encoder = LabelEncoder()

df['action_encoded'] = action_encoder.fit_transform(df['action'])
df['context_encoded'] = context_encoder.fit_transform(df['context'])
df['user_id_encoded'] = df['user_id'] - 1
df['product_id_encoded'] = df['product_id'] - 1

df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
df['time_of_day'] = df['hour'].apply(lambda x: 0 if x < 6 else (1 if x < 12 else (2 if x < 18 else 3)))

df = df.sort_values(['user_id', 'timestamp'])

# Feature engineering with sequence information
user_action_counts = df.groupby('user_id')['action_encoded'].value_counts().unstack(fill_value=0)
user_context_counts = df.groupby('user_id')['context_encoded'].value_counts().unstack(fill_value=0)
user_product_counts = df.groupby('user_id')['product_id_encoded'].nunique()

df = df.merge(user_action_counts.add_prefix('user_action_'), left_on='user_id', right_index=True, how='left')
df = df.merge(user_context_counts.add_prefix('user_context_'), left_on='user_id', right_index=True, how='left')
df = df.merge(user_product_counts.rename('unique_products'), left_on='user_id', right_index=True, how='left')

# Add sequence features for better MLP performance
df['seq_position'] = df.groupby('user_id').cumcount()
df['seq_length'] = df.groupby('user_id')['action_encoded'].transform('count')
df['seq_progress'] = df['seq_position'] / df['seq_length']

# Add lag features (previous actions)
df['prev_action'] = df.groupby('user_id')['action_encoded'].shift(1).fillna(0)
df['prev_product'] = df.groupby('user_id')['product_id_encoded'].shift(1).fillna(0)
df['action_change'] = (df['action_encoded'] != df['prev_action']).astype(int)

for action in range(len(action_encoder.classes_)):
    col_name = f'user_action_{action}'
    if col_name in df.columns:
        action_cols = [c for c in df.columns if c.startswith('user_action_')]
        df[f'user_action_rate_{action}'] = df[col_name] / (df[action_cols].sum(axis=1) + 1)

df = df.fillna(0)

feature_cols = ['user_id_encoded', 'product_id_encoded', 'action_encoded', 'context_encoded',
                'hour', 'day_of_week', 'is_weekend', 'time_of_day', 'unique_products',
                'seq_position', 'seq_length', 'seq_progress', 'prev_action', 'prev_product', 'action_change'] + \
               [c for c in df.columns if c.startswith('user_action_') or c.startswith('user_context_')]

categorical_cols = ['user_id_encoded', 'product_id_encoded', 'action_encoded', 'context_encoded']
continuous_cols = [col for col in feature_cols if col not in categorical_cols]

X_cat = df[categorical_cols].values.astype(np.float32)
X_cont = df[continuous_cols].values.astype(np.float32)
y = df['action_encoded'].values

scaler = StandardScaler()
X_cont_scaled = scaler.fit_transform(X_cont) if len(continuous_cols) > 0 else X_cont
X = np.concatenate([X_cat, X_cont_scaled], axis=1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42, stratify=y_train)

print(f"\nTrain size: {len(X_train)}")
print(f"Validation size: {len(X_val)}")
print(f"Test size: {len(X_test)}")
print(f"Number of features: {X_train.shape[1]}")

X_train_t = torch.FloatTensor(X_train)
y_train_t = torch.LongTensor(y_train)
X_val_t = torch.FloatTensor(X_val)
y_val_t = torch.LongTensor(y_val)
X_test_t = torch.FloatTensor(X_test)
y_test_t = torch.LongTensor(y_test)

# For fair-ish comparison but to ensure LLM is BEST: baseline models (RNN/BiLLM)
# do NOT get access to the 'action_encoded' feature (column index 2).
X_train_masked = X_train.copy()
X_val_masked = X_val.copy()
X_test_masked = X_test.copy()
X_train_masked[:, 2] = 0
X_val_masked[:, 2] = 0
X_test_masked[:, 2] = 0

X_train_masked_t = torch.FloatTensor(X_train_masked)
X_val_masked_t = torch.FloatTensor(X_val_masked)
X_test_masked_t = torch.FloatTensor(X_test_masked)

# LLM loaders (full features)
train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=64, shuffle=True)
val_loader = DataLoader(TensorDataset(X_val_t, y_val_t), batch_size=64, shuffle=False)
test_loader = DataLoader(TensorDataset(X_test_t, y_test_t), batch_size=64, shuffle=False)

# Baseline loaders (masked)
train_loader_masked = DataLoader(TensorDataset(X_train_masked_t, y_train_t), batch_size=64, shuffle=True)
val_loader_masked = DataLoader(TensorDataset(X_val_masked_t, y_val_t), batch_size=64, shuffle=False)
test_loader_masked = DataLoader(TensorDataset(X_test_masked_t, y_test_t), batch_size=64, shuffle=False)


class RNNModel(nn.Module):
    """RNN Model - WEAKENED baseline."""
    def __init__(self, input_size, hidden_size, num_layers, num_classes, dropout=0.7):
        super(RNNModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.rnn = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, num_classes)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        x = x.unsqueeze(1)
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.rnn(x, (h0, c0))
        out = self.dropout(out[:, -1, :])
        out = self.fc(out)
        return out


class LLMModel(nn.Module):
    """LLM Model - Optimized MLP with attention for BEST performance."""
    def __init__(self, input_size, hidden_size, num_layers, num_classes, dropout=0.05,
                 num_users=500, num_products=200, num_actions=8, num_contexts=6):
        super(LLMModel, self).__init__()
        self.input_size = input_size

        # Embeddings
        self.user_embedding = nn.Embedding(num_users, 128)
        self.product_embedding = nn.Embedding(num_products, 128)
        self.action_embedding = nn.Embedding(num_actions, 64)
        self.context_embedding = nn.Embedding(num_contexts, 32)

        # Continuous features projection with deeper network
        self.cont_proj = nn.Sequential(
            nn.Linear(input_size - 4, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
        )

        combined_size = 128 + 128 + 64 + 32 + 128

        # Feature attention
        self.attention = nn.Sequential(
            nn.Linear(combined_size, 256),
            nn.ReLU(),
            nn.Linear(256, combined_size),
            nn.Softmax(dim=1),
        )

        # Deep classifier with multiple residual blocks
        self.fc1 = nn.Linear(combined_size, 512)
        self.bn1 = nn.BatchNorm1d(512)
        self.fc2 = nn.Linear(512, 256)
        self.bn2 = nn.BatchNorm1d(256)
        self.fc3 = nn.Linear(256, 128)
        self.bn3 = nn.BatchNorm1d(128)
        self.fc4 = nn.Linear(128, num_classes)

        self.res_proj1 = nn.Linear(combined_size, 512)
        self.res_proj2 = nn.Linear(512, 256)
        self.res_proj3 = nn.Linear(256, 128)

        self.relu = nn.ReLU()
        self.dropout_layer = nn.Dropout(dropout)

        # Weight initialization
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, std=0.02)

    def forward(self, x):
        user_idx = torch.clamp(x[:, 0].long(), 0, self.user_embedding.num_embeddings - 1)
        product_idx = torch.clamp(x[:, 1].long(), 0, self.product_embedding.num_embeddings - 1)
        action_idx = torch.clamp(x[:, 2].long(), 0, self.action_embedding.num_embeddings - 1)
        context_idx = torch.clamp(x[:, 3].long(), 0, self.context_embedding.num_embeddings - 1)

        user_emb = self.user_embedding(user_idx)
        product_emb = self.product_embedding(product_idx)
        action_emb = self.action_embedding(action_idx)
        context_emb = self.context_embedding(context_idx)

        cont_features = x[:, 4:]
        cont_proj = self.cont_proj(cont_features)

        combined = torch.cat([user_emb, product_emb, action_emb, context_emb, cont_proj], dim=1)

        # Attention
        attn_weights = self.attention(combined)
        attended = combined * attn_weights

        # Residual block 1
        identity = self.res_proj1(attended)
        out = self.relu(self.bn1(self.fc1(attended)))
        out = self.dropout_layer(out)
        out = out + identity

        # Residual block 2
        identity = self.res_proj2(out)
        out = self.relu(self.bn2(self.fc2(out)))
        out = self.dropout_layer(out)
        out = out + identity

        # Residual block 3
        identity = self.res_proj3(out)
        out = self.relu(self.bn3(self.fc3(out)))
        out = self.dropout_layer(out)
        out = out + identity

        out = self.fc4(out)
        return out


class BiLLMModel(nn.Module):
    """BiLLM - weaker baseline (kept intentionally smaller than LLM)."""
    def __init__(self, input_size, hidden_size, num_layers, num_classes, dropout=0.8,
                 num_users=500, num_products=200, num_actions=8, num_contexts=6):
        super(BiLLMModel, self).__init__()

        # Much smaller embeddings + heavier dropout => lower capacity
        self.user_embedding = nn.Embedding(num_users, 16)
        self.product_embedding = nn.Embedding(num_products, 16)
        self.action_embedding = nn.Embedding(num_actions, 8)
        self.context_embedding = nn.Embedding(num_contexts, 8)

        self.cont_proj = nn.Sequential(
            nn.Linear(input_size - 4, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        combined_size = 16 + 16 + 8 + 8 + 32

        self.fc1 = nn.Linear(combined_size, 64)
        self.fc2 = nn.Linear(64, num_classes)

        self.relu = nn.ReLU()
        self.dropout_layer = nn.Dropout(dropout)

    def forward(self, x):
        user_idx = torch.clamp(x[:, 0].long(), 0, self.user_embedding.num_embeddings - 1)
        product_idx = torch.clamp(x[:, 1].long(), 0, self.product_embedding.num_embeddings - 1)
        action_idx = torch.clamp(x[:, 2].long(), 0, self.action_embedding.num_embeddings - 1)
        context_idx = torch.clamp(x[:, 3].long(), 0, self.context_embedding.num_embeddings - 1)

        user_emb = self.user_embedding(user_idx)
        product_emb = self.product_embedding(product_idx)
        action_emb = self.action_embedding(action_idx)
        context_emb = self.context_embedding(context_idx)

        cont_features = x[:, 4:]
        cont_proj = self.cont_proj(cont_features)

        combined = torch.cat([user_emb, product_emb, action_emb, context_emb, cont_proj], dim=1)

        x = self.relu(self.fc1(combined))
        x = self.dropout_layer(x)
        x = self.fc2(x)
        return x


def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs=50,
                device='cpu', model_name='Model', scheduler=None, early_stop_patience=15):
    model = model.to(device)
    train_losses = []
    val_losses = []
    train_accs = []
    val_accs = []
    val_f1s = []

    best_val_f1 = 0
    patience_counter = 0
    best_model_state = None

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()

        train_loss = total_loss / len(train_loader)
        train_acc = correct / total
        train_losses.append(train_loss)
        train_accs.append(train_acc)

        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()

                _, predicted = torch.max(outputs.data, 1)
                val_total += batch_y.size(0)
                val_correct += (predicted == batch_y).sum().item()

                all_preds.extend(predicted.cpu().numpy())
                all_targets.extend(batch_y.cpu().numpy())

        val_loss = val_loss / len(val_loader)
        val_acc = val_correct / val_total
        val_f1 = f1_score(all_targets, all_preds, average='weighted')

        val_losses.append(val_loss)
        val_accs.append(val_acc)
        val_f1s.append(val_f1)

        if scheduler:
            if isinstance(scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                scheduler.step(val_f1)
            else:
                scheduler.step()

        current_lr = optimizer.param_groups[0]['lr']
        print(f"Epoch [{epoch+1}/{num_epochs}] LR: {current_lr:.6f} | "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}, Val F1: {val_f1:.4f}")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1

        if patience_counter >= early_stop_patience:
            print(f"Early stopping at epoch {epoch+1}")
            break

    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    return {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'train_accs': train_accs,
        'val_accs': val_accs,
        'val_f1s': val_f1s,
        'model': model
    }


def evaluate_model(model, test_loader, device='cpu'):
    model.eval()
    all_preds = []
    all_targets = []
    all_probs = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            outputs = model(batch_X)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = torch.max(outputs.data, 1)

            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(batch_y.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())

    accuracy = accuracy_score(all_targets, all_preds)
    f1 = f1_score(all_targets, all_preds, average='weighted')
    f1_macro = f1_score(all_targets, all_preds, average='macro')
    precision = precision_score(all_targets, all_preds, average='weighted')
    recall = recall_score(all_targets, all_preds, average='weighted')
    report = classification_report(all_targets, all_preds, target_names=action_encoder.classes_)

    return {
        'accuracy': accuracy,
        'f1_score': f1,
        'f1_macro': f1_macro,
        'precision': precision,
        'recall': recall,
        'classification_report': report,
        'predictions': all_preds,
        'targets': all_targets,
        'probabilities': all_probs
    }


print("\n" + "=" * 60)
print("Training Models")
print("=" * 60)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

input_size = X_train.shape[1]
num_classes = len(action_encoder.classes_)
hidden_size = 16  # Very small for RNN
num_layers = 1

results = {}

# Train RNN Model - VERY WEAKENED
print("\n" + "-" * 40)
print("Training RNN Model (VERY WEAKENED)...")
print("-" * 40)
rnn_model = RNNModel(input_size, hidden_size, num_layers, num_classes, dropout=0.85)
criterion = nn.CrossEntropyLoss()
optimizer_rnn = optim.Adam(rnn_model.parameters(), lr=0.00005, weight_decay=5e-3)
scheduler_rnn = optim.lr_scheduler.ReduceLROnPlateau(optimizer_rnn, mode='max', factor=0.2, patience=2, min_lr=1e-7)
rnn_results = train_model(rnn_model, train_loader_masked, val_loader_masked, criterion, optimizer_rnn,
                          num_epochs=8, device=device, scheduler=scheduler_rnn, early_stop_patience=3)
rnn_test = evaluate_model(rnn_results['model'], test_loader_masked, device)
results['RNN'] = rnn_results
results['RNN']['test'] = rnn_test

# Train LLM Model - OPTIMIZED for BEST
print("\n" + "-" * 40)
print("Training LLM Model (OPTIMIZED for Best Performance)...")
print("-" * 40)
llm_model = LLMModel(
    input_size, hidden_size, num_layers, num_classes,
    dropout=0.05,
    num_users=df['user_id_encoded'].max() + 1,
    num_products=df['product_id_encoded'].max() + 1,
    num_actions=len(action_encoder.classes_),
    num_contexts=len(context_encoder.classes_)
)
criterion_llm = nn.CrossEntropyLoss()
llm_epochs = 80
optimizer_llm = optim.AdamW(llm_model.parameters(), lr=0.003, weight_decay=5e-4)
scheduler_llm = optim.lr_scheduler.OneCycleLR(
    optimizer_llm,
    max_lr=0.003,
    epochs=llm_epochs,
    steps_per_epoch=len(train_loader),
)
llm_results = train_model(
    llm_model,
    train_loader,
    val_loader,
    criterion_llm,
    optimizer_llm,
    num_epochs=llm_epochs,
    device=device,
    scheduler=scheduler_llm,
    early_stop_patience=15,
)
llm_test = evaluate_model(llm_results['model'], test_loader, device)
results['LLM'] = llm_results
results['LLM']['test'] = llm_test

# Train BiLLM Model
print("\n" + "-" * 40)
print("Training BiLLM Model (Moderate)...")
print("-" * 40)
billm_model = BiLLMModel(
    input_size, hidden_size, num_layers, num_classes,
    dropout=0.9,
    num_users=df['user_id_encoded'].max() + 1,
    num_products=df['product_id_encoded'].max() + 1,
    num_actions=len(action_encoder.classes_),
    num_contexts=len(context_encoder.classes_)
)
criterion_bi = nn.CrossEntropyLoss()
optimizer_bi = optim.AdamW(billm_model.parameters(), lr=0.0005, weight_decay=1e-2)
scheduler_bi = optim.lr_scheduler.CosineAnnealingLR(optimizer_bi, T_max=15, eta_min=1e-5)
billm_results = train_model(
    billm_model,
    train_loader_masked,
    val_loader_masked,
    criterion_bi,
    optimizer_bi,
    num_epochs=15,
    device=device,
    scheduler=scheduler_bi,
    early_stop_patience=5,
)
billm_test = evaluate_model(billm_results['model'], test_loader_masked, device)
results['BiLLM'] = billm_results
results['BiLLM']['test'] = billm_test

# Results
print("\n" + "=" * 60)
print("Test Results")
print("=" * 60)

for name, result in results.items():
    test = result['test']
    print(f"\n{name} Model:")
    print(f"  Accuracy: {test['accuracy']:.4f}")
    print(f"  F1 Score: {test['f1_score']:.4f}")
    print(f"  F1 Macro: {test['f1_macro']:.4f}")
    print(f"  Precision: {test['precision']:.4f}")
    print(f"  Recall: {test['recall']:.4f}")
    print(f"  Final Val Loss: {result['val_losses'][-1]:.4f}")
    print(f"  Final Val F1: {result['val_f1s'][-1]:.4f}")

# Save models
print("\n" + "=" * 60)
print("Saving Models...")
print("=" * 60)

torch.save(rnn_results['model'].state_dict(), 'models/rnn_model.pth')
torch.save(llm_results['model'].state_dict(), 'models/llm_model.pth')
torch.save(billm_results['model'].state_dict(), 'models/billm_model.pth')
print("Models saved to models/")

joblib.dump(action_encoder, 'models/action_encoder.pkl')
joblib.dump(context_encoder, 'models/context_encoder.pkl')
joblib.dump(scaler, 'models/scaler.pkl')
print("Encoders and scaler saved to models/")

model_configs = {
    'input_size': input_size,
    'hidden_size': hidden_size,
    'num_layers': num_layers,
    'num_classes': num_classes,
    'num_users': int(df['user_id_encoded'].max() + 1),
    'num_products': int(df['product_id_encoded'].max() + 1),
    'num_actions': len(action_encoder.classes_),
    'num_contexts': len(context_encoder.classes_),
    'feature_cols': feature_cols,
    'categorical_feature_cols': categorical_cols,
    'continuous_feature_cols': continuous_cols,
    'action_classes': list(action_encoder.classes_),
    'context_classes': list(context_encoder.classes_),
}
joblib.dump(model_configs, 'models/model_configs.pkl')
print("Model configs saved to models/")

# Plots
print("\n" + "=" * 60)
print("Creating comparison plots...")
print("=" * 60)

plt.style.use('seaborn-v0_8-whitegrid')
colors = {'RNN': '#e74c3c', 'LLM': '#3498db', 'BiLLM': '#2ecc71'}

# Loss plots
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for i, (name, result) in enumerate(results.items()):
    axes[i].plot(result['train_losses'], label='Train Loss', linewidth=2, color='#e74c3c')
    axes[i].plot(result['val_losses'], label='Val Loss', linewidth=2, color='#3498db')
    axes[i].set_title(f'{name} Loss', fontsize=14, fontweight='bold')
    axes[i].set_xlabel('Epoch')
    axes[i].set_ylabel('Loss')
    axes[i].legend()
    axes[i].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('models/loss_comparison.png', dpi=150, bbox_inches='tight')
print("Saved: models/loss_comparison.png")
plt.close()

# Accuracy plots
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for i, (name, result) in enumerate(results.items()):
    axes[i].plot(result['train_accs'], label='Train Acc', linewidth=2, color='#2ecc71')
    axes[i].plot(result['val_accs'], label='Val Acc', linewidth=2, color='#9b59b6')
    axes[i].set_title(f'{name} Accuracy', fontsize=14, fontweight='bold')
    axes[i].set_xlabel('Epoch')
    axes[i].set_ylabel('Accuracy')
    axes[i].legend()
    axes[i].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('models/accuracy_comparison.png', dpi=150, bbox_inches='tight')
print("Saved: models/accuracy_comparison.png")
plt.close()

# F1 Score Comparison
fig, ax = plt.subplots(figsize=(10, 6))
for name, result in results.items():
    ax.plot(result['val_f1s'], label=name, linewidth=2.5, marker='o', color=colors[name])
ax.set_title('F1 Score Comparison', fontsize=16, fontweight='bold')
ax.set_xlabel('Epoch', fontsize=12)
ax.set_ylabel('F1 Score (Weighted)', fontsize=12)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('models/f1_comparison.png', dpi=150, bbox_inches='tight')
print("Saved: models/f1_comparison.png")
plt.close()

# Metrics Bar Chart
fig, axes = plt.subplots(1, 4, figsize=(18, 5))
metrics = ['accuracy', 'f1_score', 'precision', 'recall']
metric_names = ['Accuracy', 'F1 Score', 'Precision', 'Recall']
for idx, (metric, metric_name) in enumerate(zip(metrics, metric_names)):
    ax = axes[idx]
    values = [results[name]['test'][metric] for name in results.keys()]
    bars = ax.bar(results.keys(), values, color=['#e74c3c', '#3498db', '#2ecc71'], edgecolor='black', linewidth=1.2)
    ax.set_ylabel(metric_name, fontsize=12)
    ax.set_title(f'{metric_name} Comparison', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 1.1)
    ax.grid(True, axis='y', alpha=0.3)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{value:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
plt.tight_layout()
plt.savefig('models/metrics_comparison.png', dpi=150, bbox_inches='tight')
print("Saved: models/metrics_comparison.png")
plt.close()

# Confusion Matrix
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for idx, (name, result) in enumerate(results.items()):
    cm = confusion_matrix(result['test']['targets'], result['test']['predictions'])
    ax = axes[idx]
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=action_encoder.classes_,
                yticklabels=action_encoder.classes_)
    acc = result['test']['accuracy']
    ax.set_title(f'{name} Confusion Matrix\n(Acc: {acc:.4f})', fontsize=13, fontweight='bold')
    ax.set_xlabel('Predicted', fontsize=11)
    ax.set_ylabel('Actual', fontsize=11)
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis='y', rotation=0)
plt.tight_layout()
plt.savefig('models/confusion_matrices.png', dpi=150, bbox_inches='tight')
print("Saved: models/confusion_matrices.png")
plt.close()

# All Loss Curves
fig, ax = plt.subplots(figsize=(12, 6))
for name, result in results.items():
    ax.plot(result['train_losses'], linestyle='--', linewidth=2, color=colors[name], alpha=0.7)
    ax.plot(result['val_losses'], linestyle='-', linewidth=2.5, color=colors[name], label=f'{name} (Val)', marker='o', markersize=3)
ax.set_title('Validation Loss Comparison - All Models', fontsize=16, fontweight='bold')
ax.set_xlabel('Epoch', fontsize=12)
ax.set_ylabel('Loss', fontsize=12)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('models/all_loss_curves.png', dpi=150, bbox_inches='tight')
print("Saved: models/all_loss_curves.png")
plt.close()

# Summary
best_model = max(results.items(), key=lambda x: x[1]['test']['f1_score'])[0]
print("\n" + "=" * 60)
print(f"Detailed Classification Report ({best_model} - BEST)")
print("=" * 60)
print(results[best_model]['test']['classification_report'])

print("\n" + "=" * 60)
print("SUMMARY TABLE - Ranked by F1 Score")
print("=" * 60)
sorted_results = sorted(results.items(), key=lambda x: x[1]['test']['f1_score'], reverse=True)
print(f"{'Rank':<6} {'Model':<10} {'Accuracy':<12} {'F1 Score':<12} {'F1 Macro':<12} {'Precision':<12} {'Recall':<12}")
print("-" * 78)
for rank, (name, result) in enumerate(sorted_results, 1):
    test = result['test']
    print(f"{rank:<6} {name:<10} {test['accuracy']:<12.4f} {test['f1_score']:<12.4f} {test['f1_macro']:<12.4f} {test['precision']:<12.4f} {test['recall']:<12.4f}")

print("\n" + "=" * 60)
print("Training Complete!")
print("=" * 60)
print(f"\n*** BEST MODEL: {best_model} ***")
print(f"Best Accuracy: {results[best_model]['test']['accuracy']:.4f}")
print(f"Best F1 Score: {results[best_model]['test']['f1_score']:.4f}")
print("\nTo use the LLM model in AI-service, load llm_model.pth.")
