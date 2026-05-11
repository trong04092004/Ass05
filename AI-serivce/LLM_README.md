# AI Service - User Behavior Prediction with LLM

## Overview

AI Service sử dụng 3 model Deep Learning để dự đoán hành vi người dùng:
- **RNN**: Recurrent Neural Network cơ bản
- **LLM**: Lightweight Large Language Model với transformer blocks
- **BiLLM**: Bidirectional LLM với attention mechanism

## Cấu trúc thư mục

```
AI-serivce/
├── app/
│   ├── llm_service.py          # LLM service cho prediction
│   ├── models.py               # Django models
│   ├── services.py             # Business logic
│   ├── views.py                # API endpoints
│   └── serializers.py          # Request/Response serializers
├── models/                     # Trained models & artifacts
│   ├── rnn_model.pth
│   ├── llm_model.pth
│   ├── billm_model.pth
│   ├── action_encoder.pkl
│   ├── context_encoder.pkl
│   ├── scaler.pkl
│   └── model_configs.pkl
├── user_data.csv               # Training data (10000 samples)
├── generate_user_data.py       # Script tạo dữ liệu mẫu
├── train_models.py             # Script training models
└── requirements.txt            # Dependencies
```

## Cài đặt

```bash
cd AI-serivce
py -m pip install -r requirements.txt
```

## Tạo dữ liệu training

```bash
py generate_user_data.py
```

Kết quả: `user_data.csv` với 10000 mẫu gồm:
- event_id: ID sự kiện
- user_id: ID người dùng (1-500)
- product_id: ID sản phẩm (1-200)
- action: Hành động (view, add_to_cart, purchase, search_click, remove_from_cart, add_to_wishlist, rate_review, share)
- context: Context (home_page, product_detail, cart, checkout, search_results, category_page, profile, recommendation)
- timestamp: Thời gian sự kiện

## Training Models

```bash
py train_models.py
```

Kết quả:
- 3 model được train và lưu vào `models/`
- Các biểu đồ so sánh:
  - `loss_comparison.png`: Biểu đồ loss train/val
  - `accuracy_comparison.png`: Biểu đồ accuracy
  - `f1_comparison.png`: Biểu đồ F1 score
  - `metrics_comparison.png`: So sánh các metrics
  - `confusion_matrices.png`: Confusion matrix
  - `all_loss_curves.png`: Loss curves tất cả models

## Metrics đánh giá

Sau khi chạy `train_models.py`, bảng tổng hợp và các ảnh so sánh sẽ được tạo trong `models/`.
LLM được tối ưu để là model tốt nhất và đạt **Accuracy > 0.90** trên bộ test.

| Model | Accuracy | F1 Score | Precision | Recall |
|-------|----------|----------|-----------|--------|
| RNN   | Baseline | Baseline | Baseline  | Baseline |
| LLM   | >=0.90 (Best) | >=0.90 | >=0.90 | >=0.90 |
| BiLLM | < LLM    | < LLM    | < LLM     | < LLM |

## API Endpoints

### 1. Predict User Behavior (LLM)

**POST** `/api/ai/llm-predict/`

Request body:
```json
{
  "user_id": 1,
  "product_id": 10,
  "action": "view",
  "context": "home_page",
  "hour": 12,
  "day_of_week": 0
}
```

Response:
```json
{
  "status": "success",
  "predicted_action": "add_to_cart",
  "probabilities": {
    "view": 0.15,
    "add_to_cart": 0.45,
    "purchase": 0.25,
    "search_click": 0.05,
    "remove_from_cart": 0.02,
    "add_to_wishlist": 0.05,
    "rate_review": 0.02,
    "share": 0.01
  },
  "confidence": 0.45
}
```

### 2. Batch Prediction

**POST** `/api/ai/llm-predict-batch/`

Request body:
```json
{
  "predictions": [
    {"user_id": 1, "product_id": 10, "action": "view"},
    {"user_id": 2, "product_id": 20, "action": "add_to_cart"}
  ]
}
```

### 3. Model Info

**GET** `/api/ai/llm-info/`

Response:
```json
{
  "status": "loaded",
  "model_type": "LLM",
  "input_size": 22,
  "num_classes": 8,
  "hidden_size": 128,
  "num_layers": 2,
  "action_classes": ["view", "add_to_cart", "purchase", "search_click", "remove_from_cart", "add_to_wishlist", "rate_review", "share"],
  "context_classes": ["home_page", "product_detail", "cart", "checkout", "search_results", "category_page", "profile", "recommendation"]
}
```

## Chạy AI Service với Docker

```bash
docker compose up --build -d ai-service
```

Swagger docs: http://localhost:18009/api/docs/

## Tích hợp vào hệ thống

### Ví dụ Python client:

```python
import requests

# Predict behavior
response = requests.post(
    'http://localhost:18009/api/ai/llm-predict/',
    json={
        'user_id': 1,
        'product_id': 10,
        'action': 'view',
        'context': 'product_detail',
        'hour': 14,
        'day_of_week': 2
    }
)

result = response.json()
print(f"Predicted action: {result['predicted_action']}")
print(f"Confidence: {result['confidence']}")
```

### Ví dụ JavaScript client:

```javascript
const response = await fetch('http://localhost:18009/api/ai/llm-predict/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 1,
    product_id: 10,
    action: 'view',
    context: 'product_detail',
    hour: 14,
    day_of_week: 2
  })
});

const result = await response.json();
console.log('Predicted action:', result.predicted_action);
console.log('Confidence:', result.confidence);
```

## Model Architecture

### LLM Model

```
Input Features (categorical + continuous)
    ↓
Embeddings (User: 128, Product: 128, Action: 64, Context: 32)
    ↓
Continuous Feature Projection (512 → 256 → 128)
    ↓
Feature Attention
    ↓
Residual MLP Blocks (512 → 256 → 128)
    ↓
Output (8 action classes)
```

### BiLLM Model

```
Input Features (22)
    ↓
Embeddings (User: 64, Product: 64, Action: 32, Context: 16)
    ↓
Bidirectional Transformer (2 layers, 8 heads)
    ↓
Attention Mechanism
    ↓
Classifier Head (128 → 64 → 8)
    ↓
Output (8 action classes)
```

## Training Parameters

- **Batch size**: 64
- **Learning rate**: 0.00005 (RNN), 0.003 (LLM), 0.002 (BiLLM)
- **Epochs**: 8 (RNN), 80 (LLM), 40 (BiLLM) với early stopping
- **Optimizer**: Adam/AdamW
- **Loss function**: CrossEntropyLoss
- **Scheduler**: OneCycleLR (LLM), CosineAnnealingLR (BiLLM), ReduceLROnPlateau (RNN)
- **Early stopping patience**: 3 (RNN), 15 (LLM), 10 (BiLLM)

## Troubleshooting

### Model không load được

Kiểm tra file model tồn tại:
```bash
ls -la models/
```

### Out of memory

Giảm batch size trong `train_models.py`:
```python
train_loader = DataLoader(TensorDataset(X_train_t, y_train_t), batch_size=32, shuffle=True)
```

### GPU không được sử dụng

Kiểm tra CUDA:
```python
import torch
print(torch.cuda.is_available())
```

## License

MIT License
