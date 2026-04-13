#!/usr/bin/env bash
set -euo pipefail

check_service() {
  local name="$1"
  local base="$2"
  local list_path="$3"
  local detail_template="$4"

  echo "=== CHECK ${name} ==="

  local health_json
  health_json=$(curl -fsS "${base}/health/security/")
  local fingerprint
  fingerprint=$(node -e 'let s="";process.stdin.on("data",d=>s+=d);process.stdin.on("end",()=>{const j=JSON.parse(s);process.stdout.write((j.jwt_key_fingerprint||""));});' <<<"${health_json}")
  if [[ -z "${fingerprint}" ]]; then
    echo "FAIL ${name}: missing jwt_key_fingerprint"
    exit 1
  fi
  echo "PASS health/security"

  local list_json
  list_json=$(curl -fsS "${base}${list_path}")

  local count
  count=$(node -e 'let s="";process.stdin.on("data",d=>s+=d);process.stdin.on("end",()=>{const j=JSON.parse(s);const items=Array.isArray(j)?j:(j.results||[]);process.stdout.write(String(items.length));});' <<<"${list_json}")
  if [[ "${count}" -lt 10 ]]; then
    echo "FAIL ${name}: expected >=10 items, got ${count}"
    exit 1
  fi

  local missing
  missing=$(node -e 'let s="";process.stdin.on("data",d=>s+=d);process.stdin.on("end",()=>{const j=JSON.parse(s);const items=Array.isArray(j)?j:(j.results||[]);const m=items.filter(x=>!(x&&x.image_url)).length;process.stdout.write(String(m));});' <<<"${list_json}")
  if [[ "${missing}" -ne 0 ]]; then
    echo "FAIL ${name}: ${missing} items missing image_url"
    exit 1
  fi
  echo "PASS list count=${count} and full images"

  local first_id
  first_id=$(node -e 'let s="";process.stdin.on("data",d=>s+=d);process.stdin.on("end",()=>{const j=JSON.parse(s);const items=Array.isArray(j)?j:(j.results||[]);process.stdout.write(items.length?String(items[0].id):"");});' <<<"${list_json}")
  if [[ -z "${first_id}" ]]; then
    echo "FAIL ${name}: no item available for detail smoke"
    exit 1
  fi

  local detail_path
  detail_path="${detail_template//\{id\}/${first_id}}"
  curl -fsS "${base}${detail_path}" >/dev/null
  echo "PASS detail smoke id=${first_id}"
}

check_service "book-service" "http://localhost:18002" "/books/" "/books/{id}/"
check_service "electronics-service" "http://localhost:18012" "/products/" "/products/{id}/"
check_service "fashion-service" "http://localhost:18013" "/products/" "/products/{id}/"
check_service "toy-service" "http://localhost:18014" "/products/" "/products/{id}/"
check_service "grocery-service" "http://localhost:18015" "/products/" "/products/{id}/"
check_service "furniture-service" "http://localhost:18016" "/products/" "/products/{id}/"
check_service "beauty-service" "http://localhost:18017" "/products/" "/products/{id}/"
check_service "sports-service" "http://localhost:18018" "/products/" "/products/{id}/"
check_service "pet-service" "http://localhost:18019" "/products/" "/products/{id}/"
check_service "stationery-service" "http://localhost:18020" "/products/" "/products/{id}/"

echo "ALL PRODUCT SERVICE HEALTH + SMOKE TESTS PASSED"