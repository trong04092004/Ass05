#!/usr/bin/env bash
set -euo pipefail

BASE_AUTH="http://localhost:18021"
BASE_CUSTOMER="http://localhost:18001"
BASE_BOOK="http://localhost:18002"
BASE_CART="http://localhost:18003"
BASE_ORDER="http://localhost:18004"
BASE_PAY="http://localhost:18005"
BASE_SHIP="http://localhost:18006"
BASE_COMMENT="http://localhost:18007"
BASE_CATALOG="http://localhost:18008"
BASE_STAFF="http://localhost:18009"
BASE_MANAGER="http://localhost:18010"

WAIT_TIMEOUT=360
WAIT_STEP=3

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

json_get() {
  local field="$1"
  python3 - "$field" <<'PY'
import json
import sys
field = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    print("")
    sys.exit(0)
value = data.get(field, "")
if value is None:
    value = ""
print(value)
PY
}

http_request() {
  local method="$1"
  local url="$2"
  local token="${3:-}"
  local data="${4:-}"
  local tmp_body
  tmp_body=$(mktemp)

  local -a cmd
  cmd=(curl -sS -X "$method" "$url" -o "$tmp_body" -w "%{http_code}")
  if [[ -n "$token" ]]; then
    cmd+=(-H "Authorization: Bearer $token")
  fi
  if [[ -n "$data" ]]; then
    cmd+=(-H "Content-Type: application/json" -d "$data")
  fi

  local status
  status=$("${cmd[@]}")
  local body
  body=$(cat "$tmp_body")
  rm -f "$tmp_body"
  echo "$status"$'\n'"$body"
}

assert_status() {
  local name="$1"
  local expected="$2"
  local got="$3"
  if [[ "$got" != "$expected" ]]; then
    fail "$name expected=$expected got=$got"
  fi
  echo "PASS $name = $got"
}

wait_for_service() {
  local url="$1"
  local label="$2"
  local waited=0

  while (( waited < WAIT_TIMEOUT )); do
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
    if [[ "$code" == "200" ]]; then
      echo "READY $label"
      return 0
    fi
    sleep "$WAIT_STEP"
    waited=$((waited + WAIT_STEP))
  done

  fail "Timeout waiting for $label at $url"
}

wait_for_stack() {
  wait_for_service "$BASE_CUSTOMER/health/security/" "customer-service"
  wait_for_service "$BASE_BOOK/health/security/" "book-service"
  wait_for_service "$BASE_CART/health/security/" "cart-service"
  wait_for_service "$BASE_ORDER/health/security/" "order-service"
  wait_for_service "$BASE_PAY/health/security/" "pay-service"
  wait_for_service "$BASE_SHIP/health/security/" "ship-service"
  wait_for_service "$BASE_COMMENT/health/security/" "comment-service"
  wait_for_service "$BASE_CATALOG/health/security/" "catalog-service"
  wait_for_service "$BASE_STAFF/health/security/" "staff-service"
  wait_for_service "$BASE_MANAGER/health/security/" "manager-service"
}

register_customer() {
  local suffix="$1"
  local email="customer_${suffix}@example.com"
  local payload
  payload=$(printf '{"name":"Customer %s","email":"%s","password":"Pass@123"}' "$suffix" "$email")
  local res status body
  res=$(http_request "POST" "$BASE_AUTH/auth/customer/register/" "" "$payload")
  status=$(echo "$res" | head -n1)
  body=$(echo "$res" | tail -n +2)
  assert_status "REGISTER_CUSTOMER_$suffix" "201" "$status"

  local token customer_id
  token=$(echo "$body" | json_get "access")
  customer_id=$(echo "$body" | json_get "customer_id")
  if [[ -z "$token" || -z "$customer_id" ]]; then
    fail "Could not parse customer auth payload for $suffix"
  fi

  echo "$token"$'\n'"$customer_id"
}

register_manager() {
  local suffix="$1"
  local email="manager_${suffix}@example.com"
  local payload
  payload=$(printf '{"name":"Manager %s","email":"%s","password":"Pass@123","role":"manager"}' "$suffix" "$email")

  local res status body
  res=$(http_request "POST" "$BASE_AUTH/auth/admin/register/" "" "$payload")
  status=$(echo "$res" | head -n1)
  body=$(echo "$res" | tail -n +2)
  assert_status "REGISTER_MANAGER" "201" "$status"

  local token
  token=$(echo "$body" | json_get "access")
  if [[ -z "$token" ]]; then
    fail "Could not parse manager token"
  fi
  echo "$token"
}

check_health_security() {
  local -a services=(
    "$BASE_AUTH|auth-service"
    "$BASE_CUSTOMER|customer-service"
    "$BASE_BOOK|book-service"
    "$BASE_CART|cart-service"
    "$BASE_ORDER|order-service"
    "$BASE_PAY|pay-service"
    "$BASE_SHIP|ship-service"
    "$BASE_COMMENT|comment-service"
    "$BASE_CATALOG|catalog-service"
    "$BASE_STAFF|staff-service"
    "$BASE_MANAGER|manager-service"
  )

  for entry in "${services[@]}"; do
    local base label res status body service_name fingerprint
    base="${entry%%|*}"
    label="${entry##*|}"

    res=$(http_request "GET" "$base/health/security/")
    status=$(echo "$res" | head -n1)
    body=$(echo "$res" | tail -n +2)
    assert_status "HEALTH_${label}" "200" "$status"

    service_name=$(echo "$body" | json_get "service")
    fingerprint=$(echo "$body" | json_get "jwt_key_fingerprint")

    if [[ "$service_name" != "$label" ]]; then
      fail "Unexpected service name for $label: $service_name"
    fi
    if [[ -z "$fingerprint" ]]; then
      fail "Missing jwt_key_fingerprint for $label"
    fi
    echo "PASS HEALTH_PAYLOAD_${label}"
  done
}

run_permission_matrix() {
  local seed
  seed=$(date +%s)

  local customer1 token_customer1 customer1_id
  customer1=$(register_customer "a_${seed}")
  token_customer1=$(echo "$customer1" | head -n1)
  customer1_id=$(echo "$customer1" | tail -n1)

  local customer2 token_customer2 customer2_id
  customer2=$(register_customer "b_${seed}")
  token_customer2=$(echo "$customer2" | head -n1)
  customer2_id=$(echo "$customer2" | tail -n1)

  local token_manager
  token_manager=$(register_manager "$seed")

  local res status

  res=$(http_request "GET" "$BASE_BOOK/books/")
  status=$(echo "$res" | head -n1)
  assert_status "BOOK_GET_PUBLIC" "200" "$status"

  res=$(http_request "POST" "$BASE_BOOK/books/" "" '{"title":"Denied","author":"CI","price":"10.00","stock":1}')
  status=$(echo "$res" | head -n1)
  assert_status "BOOK_POST_NOAUTH" "401" "$status"

  res=$(http_request "GET" "$BASE_CART/carts/${customer1_id}/")
  status=$(echo "$res" | head -n1)
  assert_status "CART_GET_NOAUTH" "401" "$status"

  res=$(http_request "GET" "$BASE_CART/carts/${customer1_id}/" "$token_customer1")
  status=$(echo "$res" | head -n1)
  assert_status "CART_GET_OWNER" "200" "$status"

  res=$(http_request "GET" "$BASE_CART/carts/${customer1_id}/" "$token_customer2")
  status=$(echo "$res" | head -n1)
  assert_status "CART_GET_OTHER" "403" "$status"

  res=$(http_request "POST" "$BASE_ORDER/orders/" "" "{\"customer_id\":$customer1_id}")
  status=$(echo "$res" | head -n1)
  assert_status "ORDER_POST_NOAUTH" "401" "$status"

  res=$(http_request "POST" "$BASE_ORDER/orders/" "$token_customer1" "{\"customer_id\":$customer2_id}")
  status=$(echo "$res" | head -n1)
  assert_status "ORDER_POST_MISMATCH" "403" "$status"

  res=$(http_request "POST" "$BASE_MANAGER/promotions/" "$token_customer1" '{"name":"Nope","discount_percent":5}')
  status=$(echo "$res" | head -n1)
  assert_status "PROMO_POST_CUSTOMER" "403" "$status"

  res=$(http_request "POST" "$BASE_MANAGER/promotions/" "$token_manager" '{"name":"CI Promo","discount_percent":10}')
  status=$(echo "$res" | head -n1)
  assert_status "PROMO_POST_MANAGER" "201" "$status"

  res=$(http_request "GET" "$BASE_PAY/payments/" "$token_customer1")
  status=$(echo "$res" | head -n1)
  assert_status "PAYMENT_LIST_CUSTOMER" "403" "$status"

  res=$(http_request "GET" "$BASE_PAY/payments/" "$token_manager")
  status=$(echo "$res" | head -n1)
  assert_status "PAYMENT_LIST_MANAGER" "200" "$status"

  res=$(http_request "GET" "$BASE_CUSTOMER/customers/${customer1_id}/")
  status=$(echo "$res" | head -n1)
  assert_status "CUSTOMER_DETAIL_NOAUTH" "401" "$status"

  res=$(http_request "GET" "$BASE_CUSTOMER/customers/${customer1_id}/" "$token_customer1")
  status=$(echo "$res" | head -n1)
  assert_status "CUSTOMER_DETAIL_OWNER" "200" "$status"

  res=$(http_request "GET" "$BASE_CUSTOMER/customers/${customer1_id}/" "$token_customer2")
  status=$(echo "$res" | head -n1)
  assert_status "CUSTOMER_DETAIL_OTHER" "403" "$status"

  res=$(http_request "POST" "$BASE_COMMENT/ratings/" "" "{\"book_id\":1,\"customer_id\":$customer1_id,\"rating\":5,\"comment\":\"ci\"}")
  status=$(echo "$res" | head -n1)
  assert_status "RATING_POST_NOAUTH" "401" "$status"

  res=$(http_request "POST" "$BASE_COMMENT/ratings/" "$token_customer1" "{\"book_id\":1,\"customer_id\":$customer1_id,\"rating\":5,\"comment\":\"ci\"}")
  status=$(echo "$res" | head -n1)
  assert_status "RATING_POST_AUTH" "201" "$status"
}

main() {
  wait_for_stack
  check_health_security
  run_permission_matrix
  echo "ALL CHECKS PASSED"
}

main
