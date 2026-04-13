"""
API Gateway - Views
SSR pattern: views render Django templates, goi cac microservices qua HTTP.
Session luu: customer_id, name, email, role (customer/staff/manager), access_token, refresh_token
"""
import os
import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

# --- Service URLs (doc tu env var, fallback localhost cho dev) ---
CUSTOMER_SERVICE_URL = os.environ.get('CUSTOMER_SERVICE_URL', 'http://localhost:8003')
AUTH_SERVICE_URL     = os.environ.get('AUTH_SERVICE_URL',     'http://localhost:8021')
BOOK_SERVICE_URL     = os.environ.get('BOOK_SERVICE_URL',     'http://localhost:8001')
CART_SERVICE_URL     = os.environ.get('CART_SERVICE_URL',     'http://localhost:8002')
ORDER_SERVICE_URL    = os.environ.get('ORDER_SERVICE_URL',    'http://localhost:8004')
PAY_SERVICE_URL      = os.environ.get('PAY_SERVICE_URL',      'http://localhost:8005')
SHIP_SERVICE_URL     = os.environ.get('SHIP_SERVICE_URL',     'http://localhost:8006')
COMMENT_SERVICE_URL  = os.environ.get('COMMENT_SERVICE_URL',  'http://localhost:8007')
CATALOG_SERVICE_URL  = os.environ.get('CATALOG_SERVICE_URL',  'http://localhost:8008')
MANAGER_SERVICE_URL  = os.environ.get('MANAGER_SERVICE_URL',  'http://localhost:8010')
STAFF_SERVICE_URL    = os.environ.get('STAFF_SERVICE_URL',    'http://localhost:8011')
ELECTRONICS_SERVICE_URL = os.environ.get('ELECTRONICS_SERVICE_URL', 'http://localhost:8012')
FASHION_SERVICE_URL     = os.environ.get('FASHION_SERVICE_URL',     'http://localhost:8013')
TOY_SERVICE_URL         = os.environ.get('TOY_SERVICE_URL',         'http://localhost:8014')
GROCERY_SERVICE_URL     = os.environ.get('GROCERY_SERVICE_URL',     'http://localhost:8015')
FURNITURE_SERVICE_URL   = os.environ.get('FURNITURE_SERVICE_URL',   'http://localhost:8016')
BEAUTY_SERVICE_URL      = os.environ.get('BEAUTY_SERVICE_URL',      'http://localhost:8017')
SPORTS_SERVICE_URL      = os.environ.get('SPORTS_SERVICE_URL',      'http://localhost:8018')
PET_SERVICE_URL         = os.environ.get('PET_SERVICE_URL',         'http://localhost:8019')
STATIONERY_SERVICE_URL  = os.environ.get('STATIONERY_SERVICE_URL',  'http://localhost:8020')

PRODUCT_SERVICE_URLS = {
    'electronics': ELECTRONICS_SERVICE_URL,
    'fashion': FASHION_SERVICE_URL,
    'toy': TOY_SERVICE_URL,
    'grocery': GROCERY_SERVICE_URL,
    'furniture': FURNITURE_SERVICE_URL,
    'beauty': BEAUTY_SERVICE_URL,
    'sports': SPORTS_SERVICE_URL,
    'pet': PET_SERVICE_URL,
    'stationery': STATIONERY_SERVICE_URL,
}

SECURE_COOKIES = os.environ.get('SECURE_COOKIES', 'False') == 'True'


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
            items = _get(f"{CART_SERVICE_URL}/carts/{customer_id}/", request=request) or []
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


def _session_access_token(request):
    return request.session.get('access_token') or request.session.get('token')


def _set_auth_session(request, data):
    access_token = data.get('access') or data.get('token')
    refresh_token = data.get('refresh')

    if access_token:
        request.session['access_token'] = access_token
        # Keep `token` for backward compatibility with old session keys.
        request.session['token'] = access_token
    if refresh_token:
        request.session['refresh_token'] = refresh_token


def _refresh_access_token(request):
    refresh_token = request.session.get('refresh_token')
    if not refresh_token:
        return False

    try:
        resp = requests.post(
            f"{AUTH_SERVICE_URL}/auth/token/refresh/",
            json={'refresh': refresh_token},
            timeout=5
        )
        if not resp.ok:
            return False

        data = resp.json()
        new_access = data.get('access')
        if not new_access:
            return False

        request.session['access_token'] = new_access
        request.session['token'] = new_access

        # Handle refresh rotation if customer-service enables it later.
        if data.get('refresh'):
            request.session['refresh_token'] = data.get('refresh')
        return True
    except Exception:
        return False


def _request_with_jwt(session_request, method, url, timeout=5, retry_on_401=True, **kwargs):
    headers = dict(kwargs.pop('headers', {}) or {})
    if session_request and 'Authorization' not in headers:
        access_token = _session_access_token(session_request)
        if access_token:
            headers['Authorization'] = f"Bearer {access_token}"

    response = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)

    if (
        session_request
        and retry_on_401
        and response.status_code == 401
        and _refresh_access_token(session_request)
    ):
        retry_headers = dict(headers)
        new_access = _session_access_token(session_request)
        if new_access:
            retry_headers['Authorization'] = f"Bearer {new_access}"
        response = requests.request(method, url, headers=retry_headers, timeout=timeout, **kwargs)

    return response


def _get(url, params=None, timeout=5, request=None):
    try:
        r = _request_with_jwt(request, 'GET', url, params=params, timeout=timeout)
        return r.json() if r.ok else None
    except Exception:
        return None


def _post(url, data, timeout=8, request=None):
    try:
        r = _request_with_jwt(request, 'POST', url, json=data, timeout=timeout)
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

        # If client does not pass Authorization, use current web session JWT.
        session_for_auth = None if auth else request

        if request.method == 'GET':
            resp = _request_with_jwt(session_for_auth, 'GET', url, params=request.GET, headers=headers, timeout=5)
        elif request.method == 'POST':
            resp = _request_with_jwt(session_for_auth, 'POST', url, data=request.body, headers=headers, timeout=8)
        elif request.method in ('PUT', 'PATCH'):
            resp = _request_with_jwt(session_for_auth, request.method, url, data=request.body, headers=headers, timeout=5)
        elif request.method == 'DELETE':
            resp = _request_with_jwt(session_for_auth, 'DELETE', url, headers=headers, timeout=5)
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
        if not _session_access_token(request) and not _refresh_access_token(request):
            request.session.flush()
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

def _auth_page_context(request, auth_group, error=None):
    if auth_group == 'admin':
        return {
            'error': error,
            'auth_scope': 'admin',
            'page_title': 'Admin Auth - BookStore',
            'auth_title': 'Staff/Manager Portal',
            'auth_subtitle': 'Dùng cho nhân viên và quản lý vận hành hệ thống.',
            'register_url_name': 'admin_register_page',
            'login_url_name': 'admin_login_page',
        }

    return {
        'error': error,
        'auth_scope': 'customer',
        'page_title': 'Customer Auth - BookStore',
        'auth_title': 'Customer Portal',
        'auth_subtitle': 'Dành cho khách hàng mua sách và quản lý đơn hàng cá nhân.',
        'register_url_name': 'register_page',
        'login_url_name': 'login_page',
    }

def home(request):
    books = _get(f"{BOOK_SERVICE_URL}/books/") or []
    promotions = _get(f"{MANAGER_SERVICE_URL}/promotions/") or []
    ctx = {**_session_ctx(request), 'books': books[:8], 'promotions': promotions[:3]}
    return render(request, 'home.html', ctx)


def customer_register_page(request):
    error = None
    if request.method == 'POST':
        r = _post(f"{AUTH_SERVICE_URL}/auth/customer/register/", {
            'name':     request.POST.get('name'),
            'email':    request.POST.get('email'),
            'password': request.POST.get('password'),
        }, request=request)
        if r and r.status_code in (200, 201):
            data = r.json()
            _set_auth_session(request, data)
            request.session['customer_id'] = data.get('customer_id')
            request.session['name']        = data.get('name')
            request.session['email']       = data.get('email')
            request.session['role']        = 'customer'
            return redirect('home')
        else:
            error = r.json().get('error', 'Dang ky that bai') if r else 'Khong the ket noi auth-service'
    return render(request, 'auth_register.html', _auth_page_context(request, 'customer', error))


def customer_login_page(request):
    error = None
    if request.method == 'POST':
        r = _post(f"{AUTH_SERVICE_URL}/auth/customer/login/", {
            'email':    request.POST.get('email'),
            'password': request.POST.get('password'),
        }, request=request)
        if r and r.status_code == 200:
            data = r.json()
            _set_auth_session(request, data)
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
    return render(request, 'auth_login.html', _auth_page_context(request, 'customer', error))


def admin_register_page(request):
    error = None
    if request.method == 'POST':
        role = request.POST.get('role', 'staff')
        if role not in ('staff', 'manager'):
            error = 'Vai trò không hợp lệ.'
        else:
            r = _post(f"{AUTH_SERVICE_URL}/auth/admin/register/", {
                'name':     request.POST.get('name'),
                'email':    request.POST.get('email'),
                'password': request.POST.get('password'),
                'role':     role,
            }, request=request)
            if r and r.status_code in (200, 201):
                data = r.json()
                _set_auth_session(request, data)
                request.session['customer_id'] = data.get('customer_id')
                request.session['name']        = data.get('name')
                request.session['email']       = data.get('email')
                request.session['role']        = data.get('role', 'staff')

                if request.session['role'] == 'manager':
                    return redirect('manager_dashboard')
                return redirect('staff_books')
            error = r.json().get('error', 'Dang ky that bai') if r else 'Khong the ket noi auth-service'

    ctx = _auth_page_context(request, 'admin', error)
    ctx['selected_role'] = request.POST.get('role', 'staff') if request.method == 'POST' else 'staff'
    return render(request, 'auth_register.html', ctx)


def admin_login_page(request):
    error = None
    if request.method == 'POST':
        r = _post(f"{AUTH_SERVICE_URL}/auth/admin/login/", {
            'email':    request.POST.get('email'),
            'password': request.POST.get('password'),
        }, request=request)
        if r and r.status_code == 200:
            data = r.json()
            _set_auth_session(request, data)
            request.session['customer_id'] = data.get('customer_id')
            request.session['name']        = data.get('name')
            request.session['email']       = data.get('email')
            request.session['role']        = data.get('role', 'staff')

            if request.session['role'] == 'manager':
                return redirect('manager_dashboard')
            return redirect('staff_books')
        error = 'Sai email hoac mat khau.'
    return render(request, 'auth_login.html', _auth_page_context(request, 'admin', error))


def register_page(request):
    """Legacy alias: customer register page."""
    return customer_register_page(request)


def login_page(request):
    """Legacy alias: customer login page."""
    return customer_login_page(request)


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
    items = _get(f"{CART_SERVICE_URL}/carts/{customer_id}/", request=request) or []
    total = 0
    for item in items:
        book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/", request=request) or {}
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
        }, request=request)
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
            _request_with_jwt(request, 'DELETE', f"{CART_SERVICE_URL}/cart-items/{item_id}/", timeout=5)
        except Exception:
            pass
    return redirect('my_cart')


@login_required_view
def update_cart_item(request, item_id):
    if request.method == 'POST':
        try:
            _request_with_jwt(
                request,
                'PUT',
                f"{CART_SERVICE_URL}/cart-items/{item_id}/",
                json={'quantity': int(request.POST.get('quantity', 1))},
                timeout=5
            )
        except Exception:
            pass
    return redirect('my_cart')


# ============================================================
# Checkout & Order Views (Customer)
# ============================================================

@login_required_view
def checkout(request):
    customer_id = request.session.get('customer_id')
    items = _get(f"{CART_SERVICE_URL}/carts/{customer_id}/", request=request) or []
    if not items:
        return redirect('my_cart')

    total = 0
    for item in items:
        book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/", request=request) or {}
        item['book_title'] = book.get('title', f"Book #{item['book_id']}")
        item['book_price'] = float(book.get('price', 0))
        item['subtotal']   = item['book_price'] * item.get('quantity', 1)
        total += item['subtotal']

    # Lay dia chi mac dinh cua customer
    addresses = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/", request=request) or []
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
        }, request=request)
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
    orders = _get(f"{ORDER_SERVICE_URL}/orders/customer/{customer_id}/", request=request) or []

    for order in orders:
        # Enrich voi payment + shipping + book titles
        order['payment']  = _get(f"{PAY_SERVICE_URL}/payments/order/{order['id']}/", request=request)
        order['shipping'] = _get(f"{SHIP_SERVICE_URL}/shippings/order/{order['id']}/", request=request)
        for item in order.get('items', []):
            book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/", request=request) or {}
            item['book_title'] = book.get('title', f"Book #{item['book_id']}")

    ctx = {**_session_ctx(request), 'orders': orders}
    return render(request, 'order_history.html', ctx)


# ============================================================
# Profile View (Customer)
# ============================================================

@login_required_view
def profile(request):
    customer_id = request.session.get('customer_id')
    customer = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/", request=request) or {}
    addresses = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/", request=request) or []
    success = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            r = None
            try:
                r = _request_with_jwt(
                    request,
                    'PUT',
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
            }, request=request)
            success = 'Thêm địa chỉ thành công!'
        customer  = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/", request=request) or {}
        addresses = _get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/", request=request) or []

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
            }, request=request)
            success = 'Tao sach moi thanh cong.' if (r and r.ok) else 'Loi tao sach.'
        elif action == 'delete':
            book_id = request.POST.get('book_id')
            try:
                _request_with_jwt(request, 'DELETE', f"{BOOK_SERVICE_URL}/books/{book_id}/", timeout=5)
                success = 'Da xoa sach.'
            except Exception:
                error = 'Loi xoa sach.'

    books = _get(f"{BOOK_SERVICE_URL}/books/", request=request) or []
    categories = _get(f"{CATALOG_SERVICE_URL}/categories/", request=request) or []
    ctx = {**_session_ctx(request), 'books': books, 'categories': categories,
           'error': error, 'success': success}
    return render(request, 'staff_books.html', ctx)


@staff_required
def staff_edit_book(request, book_id):
    if request.method == 'POST':
        try:
            _request_with_jwt(
                request,
                'PUT',
                f"{BOOK_SERVICE_URL}/books/{book_id}/",
                json={
                    'title':       request.POST.get('title'),
                    'author':      request.POST.get('author'),
                    'price':       request.POST.get('price'),
                    'stock':       int(request.POST.get('stock', 0)),
                    'category':    request.POST.get('category', ''),
                    'description': request.POST.get('description', ''),
                },
                timeout=5
            )
        except Exception:
            pass
    return redirect('staff_books')


@staff_required
def staff_orders(request):
    orders = _get(f"{ORDER_SERVICE_URL}/orders/", request=request) or []
    for order in orders:
        for item in order.get('items', []):
            book = _get(f"{BOOK_SERVICE_URL}/books/{item['book_id']}/", request=request) or {}
            item['book_title'] = book.get('title', f"Book #{item['book_id']}")
    ctx = {**_session_ctx(request), 'orders': orders}
    return render(request, 'staff_orders.html', ctx)


@staff_required
def staff_update_order_status(request, order_id):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        try:
            _request_with_jwt(
                request,
                'PATCH',
                f"{ORDER_SERVICE_URL}/orders/{order_id}/",
                json={'status': new_status},
                timeout=5
            )
        except Exception:
            pass
    return redirect('staff_orders')


# ============================================================
# Manager Views
# ============================================================

@manager_required
def manager_dashboard(request):
    books = _get(f"{BOOK_SERVICE_URL}/books/", request=request) or []
    orders = _get(f"{ORDER_SERVICE_URL}/orders/", request=request) or []
    customers = _get(f"{CUSTOMER_SERVICE_URL}/customers/", request=request) or []
    promotions = _get(f"{MANAGER_SERVICE_URL}/promotions/", request=request) or []
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
            }, request=request)
            success = 'Tao khuyen mai thanh cong.' if (r and r.ok) else 'Loi tao khuyen mai.'
    promotions = _get(f"{MANAGER_SERVICE_URL}/promotions/", request=request) or []
    books = _get(f"{BOOK_SERVICE_URL}/books/", request=request) or []
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
        }, request=request)
        success = 'Tạo phiếu nhập kho thành công.' if (r and r.ok) else 'Lỗi khi tạo phiếu nhập.'
    supply_orders = _get(f"{MANAGER_SERVICE_URL}/supply-orders/", request=request) or []
    books = _get(f"{BOOK_SERVICE_URL}/books/", request=request) or []
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
            }, request=request)
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
                resp = _request_with_jwt(request, 'DELETE', f"{CATALOG_SERVICE_URL}/categories/{cat_id}/", timeout=5)
                success = 'Đã xóa thể loại.' if resp.ok else 'Lỗi xóa thể loại.'
            except Exception:
                error = 'Không thể kết nối catalog-service.'
    categories = _get(f"{CATALOG_SERVICE_URL}/categories/", request=request) or []
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
            _request_with_jwt(
                request,
                'PUT',
                f"{CATALOG_SERVICE_URL}/categories/{category_id}/",
                json={
                    'name': name,
                    'slug': slug,
                    'description': desc,
                },
                timeout=5
            )
        except Exception:
            pass
    return redirect('manager_categories')


# ============================================================
# API Proxy (JSON endpoints)
# ============================================================

def _set_auth_cookies(response, payload, request):
    access_token = payload.get('access') or payload.get('token')
    refresh_token = payload.get('refresh')
    customer_id = payload.get('customer_id')
    role = payload.get('role', '')
    secure_cookie = SECURE_COOKIES or request.is_secure()

    if access_token:
        response.set_cookie(
            'access_token',
            access_token,
            max_age=60 * 30,
            httponly=True,
            secure=secure_cookie,
            samesite='Lax',
            path='/',
        )

    if refresh_token:
        response.set_cookie(
            'refresh_token',
            refresh_token,
            max_age=60 * 60 * 24 * 7,
            httponly=True,
            secure=secure_cookie,
            samesite='Lax',
            path='/',
        )

    # Role cookie is intentionally readable by frontend for client-side navigation.
    if role:
        response.set_cookie(
            'auth_role',
            role,
            max_age=60 * 60 * 24 * 7,
            httponly=False,
            secure=secure_cookie,
            samesite='Lax',
            path='/',
        )

    # Customer id cookie is readable by frontend to call customer-bound APIs.
    if customer_id is not None:
        response.set_cookie(
            'customer_id',
            str(customer_id),
            max_age=60 * 60 * 24 * 7,
            httponly=False,
            secure=secure_cookie,
            samesite='Lax',
            path='/',
        )


def _clear_auth_cookies(response, request):
    for cookie_name in ('access_token', 'refresh_token', 'auth_role', 'customer_id'):
        response.delete_cookie(
            cookie_name,
            path='/',
            samesite='Lax',
        )


def _auth_proxy_with_cookie(request, upstream_url):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        resp = requests.post(
            upstream_url,
            data=request.body,
            headers={'Content-Type': request.META.get('CONTENT_TYPE', 'application/json')},
            timeout=8,
        )
    except requests.exceptions.RequestException as exc:
        return JsonResponse({'error': f'Upstream error: {exc}'}, status=502)

    downstream = HttpResponse(
        resp.content,
        status=resp.status_code,
        content_type=resp.headers.get('Content-Type', 'application/json')
    )

    if resp.ok:
        try:
            payload = resp.json()
        except ValueError:
            payload = {}
        _set_auth_cookies(downstream, payload, request)

    return downstream

@csrf_exempt
def api_books(request):
    return _proxy(request, f"{BOOK_SERVICE_URL}/books/", ['GET', 'POST'])

@csrf_exempt
def api_book_detail(request, pk):
    return _proxy(request, f"{BOOK_SERVICE_URL}/books/{pk}/", ['GET', 'PUT', 'DELETE'])

@csrf_exempt
def api_auth_register(request):
    return _auth_proxy_with_cookie(request, f"{AUTH_SERVICE_URL}/auth/customer/register/")

@csrf_exempt
def api_auth_login(request):
    return _auth_proxy_with_cookie(request, f"{AUTH_SERVICE_URL}/auth/customer/login/")

@csrf_exempt
def api_auth_admin_register(request):
    return _auth_proxy_with_cookie(request, f"{AUTH_SERVICE_URL}/auth/admin/register/")

@csrf_exempt
def api_auth_admin_login(request):
    return _auth_proxy_with_cookie(request, f"{AUTH_SERVICE_URL}/auth/admin/login/")

@csrf_exempt
def api_auth_refresh(request):
    return _proxy(request, f"{AUTH_SERVICE_URL}/auth/token/refresh/", ['POST'])


@csrf_exempt
def api_auth_logout(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Best effort notify auth-service (future use: token blacklist/revocation).
    try:
        requests.post(
            f"{AUTH_SERVICE_URL}/auth/logout/",
            timeout=5,
            json={'refresh': request.COOKIES.get('refresh_token', '')},
        )
    except requests.exceptions.RequestException:
        pass

    request.session.flush()
    response = JsonResponse({'success': True, 'message': 'Logged out'})
    _clear_auth_cookies(response, request)
    return response

@csrf_exempt
def api_customers(request):
    return _proxy(request, f"{CUSTOMER_SERVICE_URL}/customers/", ['GET', 'POST'])


@csrf_exempt
def api_customer_detail(request, pk):
    return _proxy(request, f"{CUSTOMER_SERVICE_URL}/customers/{pk}/", ['GET', 'PUT', 'PATCH'])


@csrf_exempt
def api_customer_addresses(request, customer_id):
    return _proxy(request, f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}/addresses/", ['GET', 'POST'])

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
def api_order_detail(request, pk):
    return _proxy(request, f"{ORDER_SERVICE_URL}/orders/{pk}/", ['GET', 'PUT', 'PATCH', 'DELETE'])


@csrf_exempt
def api_orders_by_customer(request, customer_id):
    return _proxy(request, f"{ORDER_SERVICE_URL}/orders/customer/{customer_id}/", ['GET'])

@csrf_exempt
def api_ratings(request):
    return _proxy(request, f"{COMMENT_SERVICE_URL}/ratings/", ['GET', 'POST'])

@csrf_exempt
def api_ratings_list(request):
    return _proxy(request, f"{COMMENT_SERVICE_URL}/ratings/list/", ['GET'])

@csrf_exempt
def api_promotions(request):
    return _proxy(request, f"{MANAGER_SERVICE_URL}/promotions/", ['GET', 'POST'])


@csrf_exempt
def api_supply_orders(request):
    return _proxy(request, f"{MANAGER_SERVICE_URL}/supply-orders/", ['GET', 'POST'])


@csrf_exempt
def api_staff(request):
    return _proxy(request, f"{STAFF_SERVICE_URL}/staff/", ['GET', 'POST'])


@csrf_exempt
def api_categories(request):
    return _proxy(request, f"{CATALOG_SERVICE_URL}/categories/", ['GET', 'POST'])


@csrf_exempt
def api_category_detail(request, pk):
    return _proxy(request, f"{CATALOG_SERVICE_URL}/categories/{pk}/", ['GET', 'PUT', 'PATCH', 'DELETE'])


@csrf_exempt
def api_product_catalog(request, service_key):
    service_url = PRODUCT_SERVICE_URLS.get(service_key)
    if not service_url:
        return JsonResponse({'error': f'Unknown product service: {service_key}'}, status=404)
    return _proxy(request, f"{service_url}/products/", ['GET', 'POST'])


@csrf_exempt
def api_product_detail(request, service_key, pk):
    service_url = PRODUCT_SERVICE_URLS.get(service_key)
    if not service_url:
        return JsonResponse({'error': f'Unknown product service: {service_key}'}, status=404)
    return _proxy(request, f"{service_url}/products/{pk}/", ['GET', 'PUT', 'PATCH', 'DELETE'])
