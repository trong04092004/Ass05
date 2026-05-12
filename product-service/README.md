# Product Service

Unified product catalog service that manages all product types (books, electronics, fashion, beauty, etc.)

## Overview

Product Service quản lý toàn bộ danh mục sản phẩm trong hệ thống, thay thế các service riêng lẻ (book-service, electronics-service, fashion-service, beauty-service, catalog-service).

## Features

- Quản lý sản phẩm với nhiều loại khác nhau (Book, Electronics, Fashion, Beauty)
- Hỗ trợ tìm kiếm và lọc sản phẩm
- Tích hợp với AI service cho recommendation
- Dynamic attributes cho từng loại sản phẩm

## API Endpoints

- `GET /health` - Health check
- `GET /products` - List products with filtering & pagination
- `GET /products/{id}` - Get product detail
- `POST /products` - Create product (admin only)
- `PUT /products/{id}` - Update product (admin only)
- `DELETE /products/{id}` - Delete product (admin only)
- `GET /products/search?q=` - Search products
- `GET /products/suggest?q=` - Get AI recommendations

## Environment Variables

- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: ecommerce_micro_product)
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `AI_SERVICE_URL` - AI service URL for recommendations

## Running

```bash
docker compose up product-service --build
```

## Port

- 18002:8000
