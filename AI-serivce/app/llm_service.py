"""
LLM Service for AI Service - Behavior Prediction Model
Uses trained LLM model for user behavior prediction.
The model predicts next user action based on behavior patterns.
"""
import os
import numpy as np
import torch

try:
    import joblib
except Exception:
    joblib = None


MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'llm_model.pth')
ACTION_ENCODER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'action_encoder.pkl')
CONTEXT_ENCODER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'context_encoder.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'scaler.pkl')
MODEL_CONFIGS_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'model_configs.pkl')

_behavior_model = None
_model_configs = None


class LLMModel(torch.nn.Module):
    """LLM Model - attention-enhanced MLP for best performance."""
    def __init__(self, input_size, hidden_size, num_layers, num_classes, dropout=0.05,
                 num_users=500, num_products=200, num_actions=8, num_contexts=8):
        super(LLMModel, self).__init__()
        self.input_size = input_size

        self.user_embedding = torch.nn.Embedding(num_users, 128)
        self.product_embedding = torch.nn.Embedding(num_products, 128)
        self.action_embedding = torch.nn.Embedding(num_actions, 64)
        self.context_embedding = torch.nn.Embedding(num_contexts, 32)

        self.cont_proj = torch.nn.Sequential(
            torch.nn.Linear(input_size - 4, 512),
            torch.nn.BatchNorm1d(512),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(512, 256),
            torch.nn.BatchNorm1d(256),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(256, 128),
            torch.nn.BatchNorm1d(128),
            torch.nn.ReLU(),
        )

        combined_size = 128 + 128 + 64 + 32 + 128
        self.attention = torch.nn.Sequential(
            torch.nn.Linear(combined_size, 256),
            torch.nn.ReLU(),
            torch.nn.Linear(256, combined_size),
            torch.nn.Softmax(dim=1),
        )

        self.fc1 = torch.nn.Linear(combined_size, 512)
        self.bn1 = torch.nn.BatchNorm1d(512)
        self.fc2 = torch.nn.Linear(512, 256)
        self.bn2 = torch.nn.BatchNorm1d(256)
        self.fc3 = torch.nn.Linear(256, 128)
        self.bn3 = torch.nn.BatchNorm1d(128)
        self.fc4 = torch.nn.Linear(128, num_classes)

        self.res_proj1 = torch.nn.Linear(combined_size, 512)
        self.res_proj2 = torch.nn.Linear(512, 256)
        self.res_proj3 = torch.nn.Linear(256, 128)

        self.relu = torch.nn.ReLU()
        self.dropout_layer = torch.nn.Dropout(dropout)

        for m in self.modules():
            if isinstance(m, torch.nn.Linear):
                torch.nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    torch.nn.init.zeros_(m.bias)
            elif isinstance(m, torch.nn.Embedding):
                torch.nn.init.normal_(m.weight, std=0.02)

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

        attn_weights = self.attention(combined)
        attended = combined * attn_weights

        identity = self.res_proj1(attended)
        out = self.relu(self.bn1(self.fc1(attended)))
        out = self.dropout_layer(out)
        out = out + identity

        identity = self.res_proj2(out)
        out = self.relu(self.bn2(self.fc2(out)))
        out = self.dropout_layer(out)
        out = out + identity

        identity = self.res_proj3(out)
        out = self.relu(self.bn3(self.fc3(out)))
        out = self.dropout_layer(out)
        out = out + identity

        out = self.fc4(out)
        return out


def get_model_configs():
    """Load model configurations."""
    global _model_configs
    if _model_configs is not None:
        return _model_configs

    if joblib is None:
        return None

    try:
        _model_configs = joblib.load(MODEL_CONFIGS_PATH)
        return _model_configs
    except Exception:
        return None


def get_behavior_model():
    """Load or create behavior prediction model."""
    global _behavior_model

    if _behavior_model is not None:
        return _behavior_model

    if joblib is None:
        return None

    try:
        configs = get_model_configs()
        if configs is None:
            return None

        _behavior_model = LLMModel(
            input_size=configs['input_size'],
            hidden_size=configs.get('hidden_size', 16),
            num_layers=configs.get('num_layers', 1),
            num_classes=configs['num_classes'],
            dropout=0.05,
            num_users=configs.get('num_users', 500),
            num_products=configs.get('num_products', 200),
            num_actions=configs.get('num_actions', configs['num_classes']),
            num_contexts=configs.get('num_contexts', 8),
        )

        device = torch.device('cpu')
        state_dict = torch.load(MODEL_PATH, map_location=device)
        _behavior_model.load_state_dict(state_dict)
        _behavior_model.eval()

        return _behavior_model

    except Exception as e:
        print(f"Error loading model: {e}")
        return None


def _build_feature_vector(feature_cols, user_id_encoded, product_id_encoded, action_encoded, context_encoded,
                          hour, day_of_week):
    features_dict = {col: 0 for col in feature_cols}

    features_dict['user_id_encoded'] = user_id_encoded
    features_dict['product_id_encoded'] = product_id_encoded
    features_dict['action_encoded'] = action_encoded
    features_dict['context_encoded'] = context_encoded

    if 'hour' in features_dict:
        features_dict['hour'] = hour
    if 'day_of_week' in features_dict:
        features_dict['day_of_week'] = day_of_week
    if 'is_weekend' in features_dict:
        features_dict['is_weekend'] = 1 if day_of_week >= 5 else 0
    if 'time_of_day' in features_dict:
        features_dict['time_of_day'] = 0 if hour < 6 else (1 if hour < 12 else (2 if hour < 18 else 3))

    return np.array([features_dict.get(col, 0) for col in feature_cols], dtype=np.float32)


def predict_behavior(user_data):
    """
    Predict user behavior using trained model.
    Returns predicted next action and confidence scores.
    """
    model = get_behavior_model()
    if model is None:
        return {'error': 'Model not loaded', 'status': 'unavailable'}

    if joblib is None:
        return {'error': 'joblib not available', 'status': 'error'}

    try:
        configs = get_model_configs()
        if configs is None:
            return {'error': 'Configs not loaded', 'status': 'error'}

        action_enc = joblib.load(ACTION_ENCODER_PATH)
        context_enc = joblib.load(CONTEXT_ENCODER_PATH)
        scaler = joblib.load(SCALER_PATH)

        user_id = user_data.get('user_id', 1)
        product_id = user_data.get('product_id', 1)
        action = user_data.get('action', 'view')
        context = user_data.get('context', 'home_page')
        hour = int(user_data.get('hour', 12))
        day_of_week = int(user_data.get('day_of_week', 0))

        try:
            action_encoded = action_enc.transform([action])[0]
        except:
            action_encoded = 0

        try:
            context_encoded = context_enc.transform([context])[0]
        except:
            context_encoded = 0

        user_id_encoded = user_id - 1
        product_id_encoded = product_id - 1

        feature_cols = configs.get('feature_cols', [])
        if feature_cols:
            features = _build_feature_vector(
                feature_cols,
                user_id_encoded,
                product_id_encoded,
                action_encoded,
                context_encoded,
                hour,
                day_of_week,
            )
        else:
            features = np.array(
                [user_id_encoded, product_id_encoded, action_encoded, context_encoded, hour, day_of_week],
                dtype=np.float32,
            )

        continuous_cols = configs.get('continuous_feature_cols') or configs.get('continuous_cols')
        if scaler is not None and continuous_cols:
            cont_values = np.array([0.0] * len(continuous_cols), dtype=np.float32)
            for idx, col in enumerate(continuous_cols):
                if col in feature_cols:
                    cont_values[idx] = float(features[feature_cols.index(col)])
            cont_scaled = scaler.transform(cont_values.reshape(1, -1))[0]
            for idx, col in enumerate(continuous_cols):
                if col in feature_cols:
                    features[feature_cols.index(col)] = cont_scaled[idx]
        elif scaler is not None:
            features = scaler.transform(features.reshape(1, -1))[0]

        features_tensor = torch.FloatTensor(features.reshape(1, -1))

        with torch.no_grad():
            outputs = model(features_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            predicted_idx = torch.argmax(probabilities, dim=1).item()
            predicted_action = action_enc.inverse_transform([predicted_idx])[0]

        return {
            'status': 'success',
            'predicted_action': predicted_action,
            'probabilities': {
                action_enc.inverse_transform([i])[0]: round(float(prob), 4)
                for i, prob in enumerate(probabilities[0].numpy())
            },
            'confidence': round(float(probabilities[0][predicted_idx].numpy()), 4)
        }

    except Exception as e:
        return {'error': str(e), 'status': 'error'}


def predict_batch(user_data_list):
    """Predict behavior for multiple users/products."""
    results = []
    for user_data in user_data_list:
        results.append(predict_behavior(user_data))
    return results


def get_model_info():
    """Get model information."""
    configs = get_model_configs()
    if configs is None:
        return {'status': 'not_loaded'}

    return {
        'status': 'loaded',
        'model_type': 'LLM',
        'input_size': configs['input_size'],
        'num_classes': configs['num_classes'],
        'hidden_size': configs['hidden_size'],
        'num_layers': configs['num_layers'],
        'num_users': configs.get('num_users'),
        'num_products': configs.get('num_products'),
        'action_classes': configs['action_classes'],
        'context_classes': configs['context_classes'],
    }


def get_action_probabilities(user_data):
    """
    Get probability distribution over all possible next actions.
    Useful for recommendation scoring.
    """
    result = predict_behavior(user_data)
    if result.get('status') == 'success':
        return result.get('probabilities', {})
    return {}


def suggest_action_score(user_data, target_action):
    """
    Get score for a specific target action.
    Used for ranking recommendations.
    """
    probs = get_action_probabilities(user_data)
    return probs.get(target_action, 0.0)
