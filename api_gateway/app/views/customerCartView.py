import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

CART_SERVICE_URL = "http://localhost:8002"
BOOK_SERVICE_URL = "http://localhost:8001"

@api_view(['GET'])
def view_cart(request, customer_id):
    try:
        # Gọi cart-service
        cart_resp = requests.get(f"{CART_SERVICE_URL}/api/carts/{customer_id}/")
        
        if cart_resp.status_code != 200:
            return Response({"error": "Cart not found or Cart service unavailable"}, status=cart_resp.status_code)
            
        cart_data = cart_resp.json()
        
        # Bổ sung thông tin chi tiết từng cuốn sách thông qua book-service (BFF pattern)
        enriched_items = []
        total_cart_price = 0
        
        for item in cart_data.get('items', []):
            book_id = item.get('book_id')
            quantity = item.get('quantity', 1)
            
            enrich_item = {
                "id": item.get('id'),
                "book_id": book_id,
                "quantity": quantity,
                "book_details": None,
                "sub_total": 0
            }
            
            # Gọi API lấy chi tiết book
            try:
                book_resp = requests.get(f"{BOOK_SERVICE_URL}/api/books/{book_id}/")
                if book_resp.status_code == 200:
                    book_data = book_resp.json()
                    enrich_item["book_details"] = book_data
                    price = float(book_data.get('price', 0))
                    enrich_item["sub_total"] = price * quantity
                    total_cart_price += enrich_item["sub_total"]
            except requests.exceptions.RequestException:
                pass # Chấp nhận thiếu data nếu book-service die hoặc lỗi mạng
                
            enriched_items.append(enrich_item)
            
        cart_data['items'] = enriched_items
        cart_data['total_price'] = total_cart_price
        
        return Response(cart_data)
        
    except requests.exceptions.RequestException as e:
        return Response({"error": f"Failed to connect to microservices: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
