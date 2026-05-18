#!/usr/bin/env bash

set -euo pipefail

GATEWAY_BASE_URL="${GATEWAY_BASE_URL:-http://localhost:8000/auth}"
AUTH_DIRECT_URL="${AUTH_DIRECT_URL:-http://localhost:8001/auth}"
FAILURES=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GRAY='\033[0;90m'
NC='\033[0m'

sep()  { echo -e "\n${CYAN}══════════════════════════════════════════${NC}"; }
hdr()  { sep; echo -e "${YELLOW}▶ $1${NC}"; sep; }
dim()  { echo -e "${GRAY}$1${NC}"; }

pretty() {
  local text="$1"
  if echo "$text" | jq . 2>/dev/null; then
    return
  fi
  echo "$text"
}

run_test() {
  local name="$1"
  local expected="$2"
  shift 2

  local method="GET" url=""
  local args=("$@")
  for i in "${!args[@]}"; do
    case "${args[$i]}" in
      -X) method="${args[$((i+1))]}" ;;
      http*) url="${args[$i]}" ;;
    esac
  done
  dim "  → $method $url"

  local tmp_err tmp_body actual response
  tmp_err=$(mktemp)
  tmp_body=$(mktemp)

  curl -s -w "\n__STATUS__%{http_code}" "$@" >"$tmp_body" 2>"$tmp_err" || true

  actual=$(tail -n1 "$tmp_body" | sed 's/__STATUS__//')
  response=$(sed '$d' "$tmp_body")

  rm -f "$tmp_err" "$tmp_body"

  if [ "$actual" = "$expected" ]; then
    echo -e "${GREEN}✔ PASS${NC}  [$name]"
    echo -e "   ${GRAY}HTTP $actual (expected $expected)${NC}"
  else
    echo -e "${RED}✘ FAIL${NC}  [$name]"
    echo -e "   ${RED}HTTP $actual — expected $expected${NC}"
    FAILURES=$((FAILURES + 1))
  fi

  if [ -n "$response" ]; then
    echo -e "   ${GRAY}Response:${NC}"
    pretty "$response" | sed 's/^/   /'
  fi
}

# =============================================================================
# SETUP — crear admin directamente en auth-service (bypass gateway)
# =============================================================================
hdr "SETUP — Crear usuario admin en auth-service directamente"
dim "  → POST $AUTH_DIRECT_URL/admin/register"
curl -s -o /dev/null -X POST "$AUTH_DIRECT_URL/admin/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Admin Root","email":"admin@example.com","password":"AdminPass789!"}' || true
echo -e "   ${GRAY}(ignorado si ya existe)${NC}"

# =============================================================================
# 1. SIGNUP — nuevo usuario
# =============================================================================
hdr "POST /auth/signup — Registrar nuevo usuario"
run_test "signup_ok" 201 \
  -X POST "$GATEWAY_BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"SuperSecret123!"}'

# =============================================================================
# 2. SIGNUP — email duplicado
# =============================================================================
hdr "POST /auth/signup — Email duplicado (espera 409)"
run_test "signup_conflict" 409 \
  -X POST "$GATEWAY_BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"AnotherPass456!"}'

# =============================================================================
# 3. LOGIN — credenciales válidas (usuario regular)
# =============================================================================
hdr "POST /auth/login — Login usuario regular"
dim "  → POST $GATEWAY_BASE_URL/login"

LOGIN_BODY=$(mktemp)
LOGIN_STATUS=$(curl -s -o "$LOGIN_BODY" -w "%{http_code}" \
  -X POST "$GATEWAY_BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"SuperSecret123!"}')
LOGIN_RESPONSE=$(cat "$LOGIN_BODY"); rm -f "$LOGIN_BODY"

if [ "$LOGIN_STATUS" = "200" ]; then
  echo -e "${GREEN}✔ PASS${NC}  [login_user_ok]"
  echo -e "   ${GRAY}HTTP $LOGIN_STATUS (expected 200)${NC}"
else
  echo -e "${RED}✘ FAIL${NC}  [login_user_ok]"
  echo -e "   ${RED}HTTP $LOGIN_STATUS — expected 200${NC}"
  FAILURES=$((FAILURES + 1))
fi
echo -e "   ${GRAY}Response:${NC}"
pretty "$LOGIN_RESPONSE" | sed 's/^/   /'

USER_ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE"  | jq -r '.access_token')
USER_REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')

if [ -z "$USER_ACCESS_TOKEN" ] || [ "$USER_ACCESS_TOKEN" = "null" ]; then
  echo -e "${RED}✘ FAIL${NC}  [login_user_tokens] — tokens no retornados"
  FAILURES=$((FAILURES + 1))
  exit 1
fi
echo -e "\n   ${GREEN}access_token${NC}  → ${USER_ACCESS_TOKEN:0:60}..."
echo -e "   ${GREEN}refresh_token${NC} → ${USER_REFRESH_TOKEN:0:60}..."

# =============================================================================
# 4. LOGIN — credenciales inválidas
# =============================================================================
hdr "POST /auth/login — Credenciales inválidas (espera 401)"
run_test "login_bad_creds" 401 \
  -X POST "$GATEWAY_BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"WrongPassword!"}'

# =============================================================================
# 5. LOGIN — admin
# =============================================================================
hdr "POST /auth/login — Login admin"
dim "  → POST $GATEWAY_BASE_URL/login"

ADMIN_BODY=$(mktemp)
ADMIN_STATUS=$(curl -s -o "$ADMIN_BODY" -w "%{http_code}" \
  -X POST "$GATEWAY_BASE_URL/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"AdminPass789!"}')
ADMIN_RESPONSE=$(cat "$ADMIN_BODY"); rm -f "$ADMIN_BODY"

if [ "$ADMIN_STATUS" = "200" ]; then
  echo -e "${GREEN}✔ PASS${NC}  [login_admin_ok]"
  echo -e "   ${GRAY}HTTP $ADMIN_STATUS (expected 200)${NC}"
else
  echo -e "${RED}✘ FAIL${NC}  [login_admin_ok]"
  echo -e "   ${RED}HTTP $ADMIN_STATUS — expected 200${NC}"
  FAILURES=$((FAILURES + 1))
fi
echo -e "   ${GRAY}Response:${NC}"
pretty "$ADMIN_RESPONSE" | sed 's/^/   /'

ADMIN_ACCESS_TOKEN=$(echo "$ADMIN_RESPONSE"  | jq -r '.access_token')
ADMIN_REFRESH_TOKEN=$(echo "$ADMIN_RESPONSE" | jq -r '.refresh_token')

if [ -z "$ADMIN_ACCESS_TOKEN" ] || [ "$ADMIN_ACCESS_TOKEN" = "null" ]; then
  echo -e "${RED}✘ FAIL${NC}  [login_admin_tokens] — tokens no retornados"
  FAILURES=$((FAILURES + 1))
  exit 1
fi
echo -e "\n   ${GREEN}admin access_token${NC}  → ${ADMIN_ACCESS_TOKEN:0:60}..."

# =============================================================================
# 6. ME — token válido
# =============================================================================
hdr "GET /auth/me — Perfil de usuario"
run_test "me_ok" 200 \
  -X GET "$GATEWAY_BASE_URL/me" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN"

# =============================================================================
# 7. ME — sin token
# =============================================================================
hdr "GET /auth/me — Sin token (espera 401)"
run_test "me_no_token" 401 \
  -X GET "$GATEWAY_BASE_URL/me"

# =============================================================================
# 8. ME — token malformado
# =============================================================================
hdr "GET /auth/me — Token inválido (espera 401)"
run_test "me_bad_token" 401 \
  -X GET "$GATEWAY_BASE_URL/me" \
  -H "Authorization: Bearer token.invalid.here"

# =============================================================================
# 9. PATCH ME — actualizar nombre
# =============================================================================
hdr "PATCH /auth/me — Actualizar nombre"
run_test "update_me_name_ok" 200 \
  -X PATCH "$GATEWAY_BASE_URL/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -d '{"name":"John Patched"}'

# =============================================================================
# 10. PATCH ME — sin token (espera 401)
# =============================================================================
hdr "PATCH /auth/me — Sin token (espera 401)"
run_test "update_me_no_token" 401 \
  -X PATCH "$GATEWAY_BASE_URL/me" \
  -H "Content-Type: application/json" \
  -d '{"name":"Hacker"}'

# =============================================================================
# 11. PATCH ME — contraseña vieja incorrecta (espera 400)
# =============================================================================
hdr "PATCH /auth/me — Contraseña vieja incorrecta (espera 400)"
run_test "update_me_wrong_password" 400 \
  -X PATCH "$GATEWAY_BASE_URL/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -d '{"old_password":"WrongOldPass!","new_password":"NewPass456!"}'

# =============================================================================
# 12. PATCH ME — cambio de contraseña correcto
# =============================================================================
hdr "PATCH /auth/me — Cambio de contraseña correcto"
run_test "update_me_password_ok" 200 \
  -X PATCH "$GATEWAY_BASE_URL/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -d '{"old_password":"SuperSecret123!","new_password":"NewPass456!"}'

# =============================================================================
# 13. ADMIN/REGISTER — sin token (espera 401)
# =============================================================================
hdr "POST /auth/admin/register — Sin token (espera 401)"
run_test "admin_register_no_token" 401 \
  -X POST "$GATEWAY_BASE_URL/admin/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bad Actor","email":"badactor@example.com","password":"Hack123!"}'

# =============================================================================
# 14. ADMIN/REGISTER — con token de usuario regular (espera 403)
# =============================================================================
hdr "POST /auth/admin/register — Token de usuario (espera 403)"
run_test "admin_register_forbidden" 403 \
  -X POST "$GATEWAY_BASE_URL/admin/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -d '{"name":"Bad Actor","email":"badactor@example.com","password":"Hack123!"}'

# =============================================================================
# 15. ADMIN/REGISTER — con token de admin (espera 201)
# =============================================================================
hdr "POST /auth/admin/register — Token de admin (espera 201)"
run_test "admin_register_ok" 201 \
  -X POST "$GATEWAY_BASE_URL/admin/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
  -d '{"name":"Second Admin","email":"admin2@example.com","password":"Admin2Pass!"}'

# =============================================================================
# 16. GET USER BY EMAIL — con token de admin
# =============================================================================
hdr "GET /auth/user/by-email/{email} — Como admin"
dim "  → GET $GATEWAY_BASE_URL/user/by-email/john@example.com"

USER_BODY=$(mktemp)
USER_STATUS=$(curl -s -o "$USER_BODY" -w "%{http_code}" \
  -X GET "$GATEWAY_BASE_URL/user/by-email/john@example.com" \
  -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
USER_RESPONSE=$(cat "$USER_BODY"); rm -f "$USER_BODY"

USER_ID=$(echo "$USER_RESPONSE" | jq -r '.id' 2>/dev/null || true)

if [ "$USER_STATUS" = "200" ] && [ -n "$USER_ID" ] && [ "$USER_ID" != "null" ]; then
  echo -e "${GREEN}✔ PASS${NC}  [get_user_by_email_ok]"
  echo -e "   ${GRAY}HTTP $USER_STATUS (expected 200)${NC}"
  echo -e "   ${GREEN}user_id${NC} → $USER_ID"
else
  echo -e "${RED}✘ FAIL${NC}  [get_user_by_email_ok]"
  echo -e "   ${RED}HTTP $USER_STATUS — no se pudo obtener user_id${NC}"
  FAILURES=$((FAILURES + 1))
fi
echo -e "   ${GRAY}Response:${NC}"
pretty "$USER_RESPONSE" | sed 's/^/   /'

# =============================================================================
# 17. GET USER BY EMAIL — con token de usuario regular (espera 403)
# =============================================================================
hdr "GET /auth/user/by-email/{email} — Token de usuario (espera 403)"
run_test "get_user_by_email_forbidden" 403 \
  -X GET "$GATEWAY_BASE_URL/user/by-email/john@example.com" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN"

# =============================================================================
# 18. UPDATE USER — como admin
# =============================================================================
hdr "PUT /auth/user/{user_id} — Actualizar usuario como admin"
if [ -z "${USER_ID:-}" ] || [ "$USER_ID" = "null" ]; then
  echo -e "${RED}✘ SKIP${NC}  [update_user_ok] — user_id no disponible"
  FAILURES=$((FAILURES + 1))
else
  run_test "update_user_ok" 200 \
    -X PUT "$GATEWAY_BASE_URL/user/$USER_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
    -d '{"name":"John Updated"}'
fi

# =============================================================================
# 19. UPDATE USER — con token de usuario regular (espera 403)
# =============================================================================
hdr "PUT /auth/user/{user_id} — Token de usuario (espera 403)"
if [ -z "${USER_ID:-}" ] || [ "$USER_ID" = "null" ]; then
  echo -e "${RED}✘ SKIP${NC}  [update_user_forbidden] — user_id no disponible"
  FAILURES=$((FAILURES + 1))
else
  run_test "update_user_forbidden" 403 \
    -X PUT "$GATEWAY_BASE_URL/user/$USER_ID" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
    -d '{"name":"Hacked Name"}'
fi

# =============================================================================
# 20. REFRESH — renovar access token
# =============================================================================
hdr "POST /auth/refresh — Renovar access token"
dim "  → POST $GATEWAY_BASE_URL/refresh"

REFRESH_BODY=$(mktemp)
REFRESH_STATUS=$(curl -s -o "$REFRESH_BODY" -w "%{http_code}" \
  -X POST "$GATEWAY_BASE_URL/refresh" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "X-Refresh-Token: $USER_REFRESH_TOKEN")
REFRESH_RESPONSE=$(cat "$REFRESH_BODY"); rm -f "$REFRESH_BODY"

NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token' 2>/dev/null || true)

if [ -n "$NEW_ACCESS_TOKEN" ] && [ "$NEW_ACCESS_TOKEN" != "null" ]; then
  echo -e "${GREEN}✔ PASS${NC}  [refresh_ok]"
  echo -e "   ${GRAY}HTTP $REFRESH_STATUS (expected 200)${NC}"
  USER_ACCESS_TOKEN="$NEW_ACCESS_TOKEN"
  echo -e "   ${GREEN}nuevo access_token${NC} → ${USER_ACCESS_TOKEN:0:60}..."
else
  echo -e "${RED}✘ FAIL${NC}  [refresh_ok]"
  echo -e "   ${RED}HTTP $REFRESH_STATUS — nuevo token no retornado${NC}"
  FAILURES=$((FAILURES + 1))
fi
echo -e "   ${GRAY}Response:${NC}"
pretty "$REFRESH_RESPONSE" | sed 's/^/   /'

# =============================================================================
# 21. REFRESH — sin X-Refresh-Token (espera 401)
# =============================================================================
hdr "POST /auth/refresh — Sin X-Refresh-Token (espera 401)"
run_test "refresh_no_refresh_token" 401 \
  -X POST "$GATEWAY_BASE_URL/refresh" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN"

# =============================================================================
# 22. LOGOUT
# =============================================================================
hdr "POST /auth/logout — Cerrar sesión"
run_test "logout_ok" 200 \
  -X POST "$GATEWAY_BASE_URL/logout" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "X-Refresh-Token: $USER_REFRESH_TOKEN"

# =============================================================================
# 23. ME — token revocado tras logout (espera 401)
# =============================================================================
hdr "GET /auth/me — Token revocado tras logout (espera 401)"
run_test "me_revoked" 401 \
  -X GET "$GATEWAY_BASE_URL/me" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN"

# =============================================================================
# 24. REFRESH — tokens revocados tras logout (espera 401)
# =============================================================================
hdr "POST /auth/refresh — Tokens revocados tras logout (espera 401)"
run_test "refresh_revoked" 401 \
  -X POST "$GATEWAY_BASE_URL/refresh" \
  -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
  -H "X-Refresh-Token: $USER_REFRESH_TOKEN"

# =============================================================================
# 25. DELETE USER — como admin
# =============================================================================
hdr "DELETE /auth/user/{user_id} — Eliminar usuario como admin"
if [ -z "${USER_ID:-}" ] || [ "$USER_ID" = "null" ]; then
  echo -e "${RED}✘ SKIP${NC}  [delete_user_ok] — user_id no disponible"
  FAILURES=$((FAILURES + 1))
else
  run_test "delete_user_ok" 200 \
    -X DELETE "$GATEWAY_BASE_URL/user/$USER_ID" \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN"
fi

# =============================================================================
# 26. DELETE USER — usuario ya eliminado (espera 404)
# =============================================================================
hdr "DELETE /auth/user/{user_id} — Usuario inexistente (espera 404)"
if [ -z "${USER_ID:-}" ] || [ "$USER_ID" = "null" ]; then
  echo -e "${RED}✘ SKIP${NC}  [delete_user_not_found] — user_id no disponible"
  FAILURES=$((FAILURES + 1))
else
  run_test "delete_user_not_found" 404 \
    -X DELETE "$GATEWAY_BASE_URL/user/$USER_ID" \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN"
fi

# =============================================================================
# Summary
# =============================================================================
sep
TOTAL=26
PASSED=$((TOTAL - FAILURES))
echo -e "\n${YELLOW}Results:${NC} ${GREEN}${PASSED} passed${NC} · ${RED}${FAILURES} failed${NC} · ${TOTAL} total\n"

if [ "$FAILURES" -eq 0 ]; then
  echo -e "${GREEN}✔ All tests passed.${NC}\n"
  exit 0
else
  echo -e "${RED}✘ ${FAILURES} test(s) failed.${NC}\n"
  exit 1
fi
