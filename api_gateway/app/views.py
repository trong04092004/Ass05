"""
API Gateway - Views
SSR pattern: views render Django templates, goi cac microservices qua HTTP.
Session luu: customer_id, name, email, role (customer/staff/manager), token
"""
import os
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

# --- Service URLs (doc tu env var, fallback localhost cho dev) ---
CUSTOMER_SERVICE_URL = os.environ.get('CUSTOMER_SERVICE_URL', 'http://localhost:8003')
BOOK_SERVICE_URL     = os.environ.get('BOOK_SERVICE_URL',     'http://localhost:8001')
CART_SERVICE_URL     = os.environ.get('CART_SERVICE_URL',     'http://localhost:8002')
ORDER_SERVICE_URL    = os.environ.get('ORDER_SERVICE_URL',    'http://localhost:8004')
PAY_SERVICE_URL      = os.environ.get('PAY_SERVICE_URL',      'http://localhost:8005')
SHIP_SERVICE_URL     = os.environ.get('SHIP_SERVICE_URL',     'http://localhost:8006')
COMMENT_SERVICE_URL  = os.environ.get('COMMENT_SERVICE_URL',  'http://localhost:8007')
CATALOG_SERVICE_URL  = os.environ.get('CATALOG_SERVICE_URL',  'http://localhost:8008')
MANAGER_SERVICE_URL  = os.environ.get('MANAGER_SERVICE_URL',  'http://localhost:8010')


# ============================================================
# Helper functions
# ============================================================

def _session_ctx(request):
    """Context chung cho tat ca templates (session info + cart count)."""
    customer_id = request.session.get('customer_id')
    role = request.session.get('role')
    cart_count = 0
    if customer_id and role == 'customer':
        try:
            items = _get(f"{CART_SERVICE_URL}/carts/{customer_id}/") or []
            cart_count = sum(item.get('quantity', 1) for item in items)
        except Exception:
            pass
    return {
        'customer_id': customer_id,
        'name':        request.session.get('name'),
        'email':       request.session.get('email'),
        'role':        role,
        'is_staff':    role in ('staff', 'manager'),
        'is_manager':  role == 'manager',
        'cart_count':  cart_count,
    }


def _get(url, params=None, timeout=5):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        return r.json() if r.ok else None
    except Exception:
        return None


def _post(url, data, timeout=8):
    try:
        r = requests.post(url, json=data, timeout=timeout)
        return r
    except Exception:
        return None


def _proxy(request, url, allowed_methods=None):
    """Forward JSON request tu client -> service noi bo."""
    if allowed_methods and request.method not in allowed_methods:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        headers = {}
        ct = request.META.get('CONTENT_TYPE')
        if ct:
            headers['Content-Type'] = ct
        auth = request.META.get('HTTP_AUTHORIZATION')
        if auth:
            headers['Authorization'] = auth

        if request.method == 'GET':
            resp = requests.get(url, params=request.GET, timeout=5)
        elif request.method == 'POST':
            resp = requests.post(url, data=request.body, headers=headers, timeout=8)
        elif request.method in ('PUT', 'PATCH'):
            resp = requests.request(request.method, url, data=request.body, headers=headers, timeout=5)
        elif request.method == 'DELETE':
            resp = requests.delete(url, timeout=5)
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)

        return HttpResponse(
            resp.content, status=resp.status_code,
            content_type=resp.headers.get('Content-Type', 'application/json')
        )
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Upstream error: {e}'}, status=502)


def login_required_view(func):
    """Decorator: yeu cau dang nhap."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('customer_id'):
            return redirect('login_page')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def staff_required(func):
    """Decorator: yeu cau role staff hoac manager."""
    def wrapper(request, *args, **kwargs):
        if request.session.get('role') not in ('staff', 'manager'):
            return redirect('home')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def manager_required(func):
    """Decorator: yeu cau role manager."""
    def wrapper(request, *args, **kwargs):
        if request.session.get('role') != 'manager':
            return redirect('home')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# ============================================================
# Auth Views
# ============================================================

def home(request):
    books = _get(f"{BOOK_SERVICE_URL}/books/") or []
    promotions = _get(f"{MANAGER_SERVICE_URL}/promotions/") or []
    ctx = {**_session_ctx(request), 'books': books[:8], 'promotions': promotions[:3]}
    return render(request, 'home.html', ctx)


def register_page(request):
    error = None
    if request.method == 'POST':
        r = _post(f"{CUSTOMER_SERVICE_URL}/auth/register/", {
            'name':     request.POST.get('name'),
            'email':    request.POST.get('email'),
            'password': request.POST.get('password'),
            'role':     'customer',
        })
        if r and r.status_code in (200, 201):
            data = r.json()
            request.session['token']       = data.get('token')
            request.session['customer_id'] = data.get('customer_id')
            request.session['name']        = data.get('name')
            request.session['email']       = data.get('email')
            request.session['role']        = 'customer'
            return redirect('home')
        else:
            error = r.json().get('error', 'Dang ky that bai') if r else 'Khong the ket noi customer-service'
    return render(request, 'auth_register.html', {'error': error})


def login_page(request):
    error = None
    if request.method == 'POST':
        r = _post(f"{CUSTOMER_SERVICE_URL}/auth/login/", {
            'email':    request.POST.get('email'),
            'password': request.POST.get('password'),
        })
        if r and r.status_code == 200:
            data = r.json()
            request.session['token']       = data.get('token')
            request.session['customer_id'] = data.get('customer_id')
            request.session['name']        = data.get('name')
            request.session['email']       = data.get('email')
            request.session['role']        = data.get('role', 'customer')

            role = data.get('role', 'customer')
            if role == 'manager':
                return redirect('manager_dashboard')
            elif role == 'staff':
                return redirect('staff_books')
            else:
                return redirect('home')
        else:
            error = 'Sai email hoac mat khau.'
    return render(request, 'auth_login.html', {'error': error})


def logout_view(request):
    request.session.flush()
    return redirect('home')


# ============================================================
# Book Views (Customer)
# ============================================================

def book_list(request):
    q = request.GET.get('q', '')
    category = request.GET.get('category', '')
    books = _get(f"{BOOK_SERVICE_URL}/books/") or []
    categories = _get(f"{CATALOG_SERVICE_URL}/categories/") or []

    if q:
        books = [b for b in books if q.lower() in b.get('title', '').lower()
                 or q.lower() in b.get('author', '').lower()]
    if category:
        books = [b for b in books if b.get('category') == category]

    ctx = {**_session_ctx(request), 'books': books, 'categories': categories,
           'q': q, 'selected_category': category}
    return render(request, 'books.html', ctx)


def book_detail(request, book_id):
    book = _get(f"{BOOK_SERVICE_URL}/books/{book_id}/")
    if not book:
        return redirect('book_list')

    ratings = _get(f"{COMMENT_SERVICE_URL}/ratings/list/", params={'book_id': book_id}) or []
    avg = round(sum(r.get('rating', 0) for r in ratings) / len(ratings), 1) if ratings else 0
    customer_id = request.session.get('customer_id')
    already_rated = any(r.get('customer_id') == customer_id for r in ratings) if customer_id else False

    promotions = _get(f"{MANAGER_SERVICE_URL}/promotions/") or []
    promo = next((p for p in promotions if str(p.get('book_id')) == str(book_id)), None)

    ctx = {**_session_ctx(request), 'book': book, 'ratings': ratings,
           'avg_rating': avg, 'already_rated': already_rated, 'promo': promo}
    return render(request, 'book_detail.html', ctx)


def rate_book(request, book_id):
    customer_id = request.session.get('customer_id')
    if not customer_id:
        return redirect('login_page')
    if request.method == 'POST':
        _post(f"{COMMENT_SERVICE_URL}/ratings/", {
            'book_id': book_id,
            'customer_id': customer_id,
            'rating': int(request.POST.get('rating', 5)),
            'comment': request.POST.get('comment', ''),
        })
    return redirect('book_detail', book_id=book_id)


# ============================================================
# Cart Views
# ============================================================

@login_required_view
def my_cart(request):
    customer_id = request.session.get('customer_id')
    items = _get(f"{CART_SERVICE_URL}/carts/{customer_id}/") or []
    total = 0
    for item in items:
        book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/") or {}
        item['book_title'] = book.get('title', f"Book #{item['book_id']}")
        item['book_price'] = float(book.get('price', 0))
        item['subtotal']   = item['book_price'] * item.get('quantity', 1)
        total += item['subtotal']
    ctx = {**_session_ctx(request), 'items': items, 'total': total, 'customer_id': customer_id}
    return render(request, 'cart.html', ctx)


@login_required_view
def add_to_cart(request, book_id):
    customer_id = request.session.get('customer_id')
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        r = _post(f"{CART_SERVICE_URL}/cart-items/", {
            'customer_id': customer_id,
            'book_id': book_id,
            'quantity': qty,
        })
        if r and r.ok:
            request.session['cart_msg'] = f'Đã thêm {qty} cuốn vào giỏ hàng!'
        else:
            request.session['cart_msg'] = 'Lỗi khi thêm vào giỏ hàng.'
    # Redirect ve trang truoc (book_detail hoac book_list), KHONG sang gio hang
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
    if next_url:
        return redirect(next_url)
    return redirect('book_list')


@login_required_view
def remove_cart_item(request, item_id):
    if request.method == 'POST':
        try:
            requests.delete(f"{CART_SERVICE_URL}/cart-items/{item_id}/", timeout=5)
        except Exception:
            pass
    return redirect('my_cart')


@login_required_view
def update_cart_item(request, item_id):
    if request.method == 'POST':
        try:
            requests.put(f"{CART_SERVICE_URL}/cart-items/{item_id}/",
                         json={'quantity': int(request.POST.get('quantity', 1))}, timeout=5)
        except Exception:
            pass
    return redirect('my_cart')


# ============================================================
# Checkout & Order Views (Customer)
# ============================================================

@login_required_view
def checkout(request):
    customer_id = request.session.get('customer_id')
    items = _get(f"{CART_SERVICE_URL}/carts/{customer_id}/") or []
    if not items:
        return redirect('my_cart')

    total = 0
    for item in items:
        book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/") or {}
        item['book_title'] = book.get('title', f"Book #{item['book_id']}")
        item['book_price'] = float(book.get('price', 0))
        item['subtotal']   = item['book_price'] * item.get('quantity', 1)
        total += item['subtotal']

    # Lay dia chi mac dinh cua customer
    addresses = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/") or []
    default_addr = next((a for a in addresses if a.get('is_default')), addresses[0] if addresses else None)

    # Lay loi tu session (neu co, sau khi place_order that bai redirect ve day)
    error = request.session.pop('checkout_error', None)

    ctx = {**_session_ctx(request), 'items': items, 'total': total,
           'addresses': addresses, 'default_addr': default_addr, 'error': error}
    return render(request, 'checkout.html', ctx)


@login_required_view
def place_order(request):
    customer_id = request.session.get('customer_id')
    if request.method == 'POST':
        r = _post(f"{ORDER_SERVICE_URL}/orders/", {
            'customer_id':     customer_id,
            'payment_method':  request.POST.get('payment_method', 'cod'),
            'shipping_method': request.POST.get('shipping_method', 'standard'),
            'address':         request.POST.get('address', ''),
            'phone':           request.POST.get('phone', ''),
        })
        if r and r.status_code in (200, 201):
            order_data = r.json()
            PAY_MAP  = {'cod': 'COD (Thu tien khi giao)', 'bank': 'Chuyen khoan ngan hang', 'card': 'The tin dung'}
            SHIP_MAP = {'standard': 'Tieu chuan (3-5 ngay)', 'express': 'Nhanh (1-2 ngay)'}
            ctx = {**_session_ctx(request), 'order': order_data,
                   'payment_display': PAY_MAP.get(request.POST.get('payment_method', 'cod'), ''),
                   'shipping_display': SHIP_MAP.get(request.POST.get('shipping_method', 'standard'), '')}
            return render(request, 'order_success.html', ctx)
        else:
            err = r.json().get('error', 'Đặt hàng thất bại, vui lòng thử lại.') if r else 'Lỗi kết nối order-service'
            request.session['checkout_error'] = err
            return redirect('checkout')
    return redirect('checkout')


@login_required_view
def order_history(request):
    customer_id = request.session.get('customer_id')
    orders = _get(f"{ORDER_SERVICE_URL}/orders/customer/{customer_id}/") or []

    for order in orders:
        # Enrich voi payment + shipping + book titles
        order['payment']  = _get(f"{PAY_SERVICE_URL}/payments/order/{order['id']}/")
        order['shipping'] = _get(f"{SHIP_SERVICE_URL}/shippings/order/{order['id']}/")
        for item in order.get('items', []):
            book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/") or {}
            item['book_title'] = book.get('title', f"Book #{item['book_id']}")

    ctx = {**_session_ctx(request), 'orders': orders}
    return render(request, 'order_history.html', ctx)


# ============================================================
# Profile View (Customer)
# ============================================================

@login_required_view
def profile(request):
    customer_id = request.session.get('customer_id')
    customer = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/") or {}
    addresses = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/") or []
    success = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            r = None
            try:
                r = requests.put(
                    f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/",
                    json={
                        'name':  request.POST.get('name'),
                        'phone': request.POST.get('phone'),
                        'email': request.POST.get('email'),
                    }, timeout=5
                )
            except Exception:
                pass
            if r and r.ok:
                request.session['name'] = request.POST.get('name')
                success = 'Cập nhật thông tin thành công!'
            else:
                error = 'Cập nhật thất bại.'
        elif action == 'add_address':
            _post(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/", {
                'customer': customer_id,
                'label':    request.POST.get('label', 'Nhà'),
                'street':   request.POST.get('street', ''),
                'district': request.POST.get('district', ''),
                'city':     request.POST.get('city', 'TP. Hồ Chí Minh'),
                'is_default': request.POST.get('is_default') == 'on',
            })
            success = 'Thêm địa chỉ thành công!'
        customer  = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/") or {}
        addresses = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/") or []

    ctx = {**_session_ctx(request), 'customer': customer, 'addresses': addresses,
           'success': success, 'error': error}
    return render(request, 'profile.html', ctx)


# ============================================================
# Staff Views
# ============================================================

@staff_required
def staff_books(request):
    error = None
    success = None
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'create':
            r = _post(f"{BOOK_SERVICE_URL}/books/", {
                'title':  request.POST.get('title'),
                'author': request.POST.get('author'),
                'price':  request.POST.get('price'),
                'stock':  int(request.POST.get('stock', 0)),
                'category': request.POST.get('category', ''),
                'description': request.POST.get('description', ''),
            })
            success = 'Tao sach moi thanh cong.' if (r and r.ok) else 'Loi tao sach.'
        elif action == 'delete':
            book_id = request.POST.get('book_id')
            try:
                requests.delete(f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
                success = 'Da xoa sach.'
            except Exception:
                error = 'Loi xoa sach.'

    books = _get(f"{BOOK_SERVICE_URL}/books/") or []
    categories = _get(f"{CATALOG_SERVICE_URL}/categories/") or []
    ctx = {**_session_ctx(request), 'books': books, 'categories': categories,
           'error': error, 'success': success}
    return render(request, 'staff_books.html', ctx)


@staff_required
def staff_edit_book(request, book_id):
    if request.method == 'POST':
        try:
            requests.put(f"{BOOK_SERVICE_URL}/books/{book_id}/", json={
                'title':       request.POST.get('title'),
                'author':      request.POST.get('author'),
                'price':       request.POST.get('price'),
                'stock':       int(request.POST.get('stock', 0)),
                'category':    request.POST.get('category', ''),
                'description': request.POST.get('description', ''),
            }, timeout=5)
        except Exception:
            pass
    return redirect('staff_books')


@staff_required
def staff_orders(request):
    orders = _get(f"{ORDER_SERVICE_URL}/orders/") or []
    for order in orders:
        for item in order.get('items', []):
            book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/") or {}
            item['book_title'] = book.get('title', f"Book #{item['book_id']}")
    ctx = {**_session_ctx(request), 'orders': orders}
    return render(request, 'staff_orders.html', ctx)


@staff_required
def staff_update_order_status(request, order_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        try:
            requests.patch(f"{ORDER_SERVICE_URL}/orders/{order_id}/", 
                           json={'status': new_status}, timeout=5)
        except Exception:
            pass
    return redirect('staff_orders')


# ============================================================
# Manager Views
# ============================================================

@manager_required
def manager_dashboard(request):
    books = _get(f"{BOOK_SERVICE_URL}/books/") or []
    orders = _get(f"{ORDER_SERVICE_URL}/orders/") or []
    customers = _get(f"{CUSTOMER_SERVICE_URL}/customers/") or []
    promotions = _get(f"{MANAGER_SERVICE_URL}/promotions/") or []
    ctx = {**_session_ctx(request), 'books': books, 'orders': orders,
           'customers': customers, 'promotions': promotions}
    return render(request, 'manager_dashboard.html', ctx)


@manager_required
def manager_promotions(request):
    error = None
    success = None
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'create':
            r = _post(f"{MANAGER_SERVICE_URL}/promotions/", {
                'name':            request.POST.get('name'),
                'discount_percent': request.POST.get('discount_percent', 0),
                'book_id':         request.POST.get('book_id', ''),
                'start_date':      request.POST.get('start_date', ''),
                'end_date':        request.POST.get('end_date', ''),
            })
            success = 'Tao khuyen mai thanh cong.' if (r and r.ok) else 'Loi tao khuyen mai.'
    promotions = _get(f"{MANAGER_SERVICE_URL}/promotions/") or []
    books = _get(f"{BOOK_SERVICE_URL}/books/") or []
    ctx = {**_session_ctx(request), 'promotions': promotions, 'books': books,
           'error': error, 'success': success}
    return render(request, 'manager_promotions.html', ctx)


@staff_required
def manager_inventory(request):
    """Nhap kho - chuyen sang staff_required (nhan vien thuc hien nhap kho)."""
    error = None
    success = None
    if request.method == 'POST':
        r = _post(f"{MANAGER_SERVICE_URL}/supply-orders/", {
            'book_id':  request.POST.get('book_id'),
            'quantity': int(request.POST.get('quantity', 0)),
            'supplier': request.POST.get('supplier', ''),
            'note':     request.POST.get('note', ''),
        })
        success = 'Tạo phiếu nhập kho thành công.' if (r and r.ok) else 'Lỗi khi tạo phiếu nhập.'
    supply_orders = _get(f"{MANAGER_SERVICE_URL}/supply-orders/") or []
    books = _get(f"{BOOK_SERVICE_URL}/books/") or []
    ctx = {**_session_ctx(request), 'supply_orders': supply_orders, 'books': books,
           'error': error, 'success': success}
    return render(request, 'manager_inventory.html', ctx)


@manager_required
def manager_categories(request):
    """Quan ly the loai sach - chi Manager."""
    error = None
    success = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_category':
            name = request.POST.get('name', '').strip()
            desc = request.POST.get('description', '').strip()
            # Auto-generate slug from name
            import re
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            r = _post(f"{CATALOG_SERVICE_URL}/categories/", {
                'name': name,
                'slug': slug,
                'description': desc,
            })
            if r and r.ok:
                success = f'Đã tạo thể loại «{name}» thành công.'
            else:
                err_detail = ''
                try:
                    err_detail = r.json() if r else ''
                except Exception:
                    pass
                error = f'Lỗi tạo thể loại: {err_detail}'
        elif action == 'delete_category':
            cat_id = request.POST.get('category_id')
            try:
                resp = requests.delete(f"{CATALOG_SERVICE_URL}/categories/{cat_id}/", timeout=5)
                success = 'Đã xóa thể loại.' if resp.ok else 'Lỗi xóa thể loại.'
            except Exception:
                error = 'Không thể kết nối catalog-service.'
    categories = _get(f"{CATALOG_SERVICE_URL}/categories/") or []
    ctx = {**_session_ctx(request), 'categories': categories,
           'error': error, 'success': success}
    return render(request, 'manager_categories.html', ctx)


@manager_required
def manager_categories_update(request, category_id):
    """Cap nhat ten/mo ta the loai."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        desc = request.POST.get('description', '').strip()
        import re
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        try:
            requests.put(f"{CATALOG_SERVICE_URL}/categories/{category_id}/", json={
                'name': name,
                'slug': slug,
                'description': desc,
            }, timeout=5)
        except Exception:
            pass
    return redirect('manager_categories')


# ============================================================
# API Proxy (JSON endpoints)
# ============================================================

@csrf_exempt
def api_books(request):
    return _proxy(request, f"{BOOK_SERVICE_URL}/books/", ['GET', 'POST'])

@csrf_exempt
def api_book_detail(request, pk):
    return _proxy(request, f"{BOOK_SERVICE_URL}/books/{pk}/", ['GET', 'PUT', 'DELETE'])

@csrf_exempt
def api_auth_register(request):
    return _proxy(request, f"{CUSTOMER_SERVICE_URL}/auth/register/", ['POST'])

@csrf_exempt
def api_auth_login(request):
    return _proxy(request, f"{CUSTOMER_SERVICE_URL}/auth/login/", ['POST'])

@csrf_exempt
def api_customers(request):
    return _proxy(request, f"{CUSTOMER_SERVICE_URL}/customers/", ['GET', 'POST'])

@csrf_exempt
def api_cart(request, customer_id):
    return _proxy(request, f"{CART_SERVICE_URL}/carts/{customer_id}/", ['GET'])

@csrf_exempt
def api_cart_items(request):
    return _proxy(request, f"{CART_SERVICE_URL}/cart-items/", ['POST'])

@csrf_exempt
def api_cart_item_detail(request, pk):
    return _proxy(request, f"{CART_SERVICE_URL}/cart-items/{pk}/", ['PUT', 'PATCH', 'DELETE'])

@csrf_exempt
def api_orders(request):
    return _proxy(request, f"{ORDER_SERVICE_URL}/orders/", ['GET', 'POST'])

@csrf_exempt
def api_ratings(request):
    return _proxy(request, f"{COMMENT_SERVICE_URL}/ratings/", ['GET', 'POST'])

@csrf_exempt
def api_ratings_list(request):
    return _proxy(request, f"{COMMENT_SERVICE_URL}/ratings/list/", ['GET'])

@csrf_exempt
def api_promotions(request):
    return _proxy(request, f"{MANAGER_SERVICE_URL}/promotions/", ['GET', 'POST'])
