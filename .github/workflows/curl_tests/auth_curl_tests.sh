

set -euo pipefail

BASE_URL="${AUTH_BASE_URL:-http://localhost:8001/auth}"
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

# Pretty-prints a JSON response, falling back to raw text.
pretty() {
  local text="$1"
  if echo "$text" | jq . 2>/dev/null; then
    return
  fi
  echo "$text"
}

# Runs a curl request and validates the expected HTTP status.
# Usage: run_test "name" EXPECTED_STATUS curl_args...
run_test() {
  local name="$1"
  local expected="$2"
  shift 2

  # Extract method + URL from args for display
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

  # Always show response body
  if [ -n "$response" ]; then
    echo -e "   ${GRAY}Response:${NC}"
    pretty "$response" | sed 's/^/   /'
  fi
}

# =============================================================================
# 1. SIGNUP — new user
# =============================================================================
hdr "POST /auth/signup — Register new user"
run_test "signup_ok" 201 \
  -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: req-signup-001" \
  -d '{"name":"John Doe","email":"john@example.com","password":"SuperSecret123!"}' \

# =============================================================================
# 2. SIGNUP — duplicate email
# =============================================================================
hdr "POST /auth/signup — Duplicate email (expects 409)"
run_test "signup_conflict" 409 \
  -X POST "$BASE_URL/signup" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: req-signup-002" \
  -d '{"name":"John Doe","email":"john@example.com","password":"AnotherPass456!"}' \

# =============================================================================
# 3. REGISTER ADMIN
# =============================================================================
hdr "POST /auth/admin/register — Register admin user"
run_test "admin_register_ok" 201 \
  -X POST "$BASE_URL/admin/register" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: req-admin-001" \
  -d '{"name":"Admin Root","email":"admin@example.com","password":"AdminPass789!"}' \

# =============================================================================
# 4. LOGIN — valid credentials
# =============================================================================
hdr "POST /auth/login — Successful login"
dim "  → POST $BASE_URL/login"

LOGIN_BODY=$(mktemp)
LOGIN_STATUS=$(curl -s -o "$LOGIN_BODY" -w "%{http_code}" \
  -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: req-login-001" \
  -d '{"email":"john@example.com","password":"SuperSecret123!"}')
LOGIN_RESPONSE=$(cat "$LOGIN_BODY"); rm -f "$LOGIN_BODY"

if [ "$LOGIN_STATUS" = "200" ]; then
  echo -e "${GREEN}✔ PASS${NC}  [login_ok]"
  echo -e "   ${GRAY}HTTP $LOGIN_STATUS (expected 200)${NC}"
else
  echo -e "${RED}✘ FAIL${NC}  [login_ok]"
  echo -e "   ${RED}HTTP $LOGIN_STATUS — expected 200${NC}"
  FAILURES=$((FAILURES + 1))
fi

echo -e "   ${GRAY}Response:${NC}"
pretty "$LOGIN_RESPONSE" | sed 's/^/   /'

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE"  | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
  echo -e "${RED}✘ FAIL${NC}  [login_tokens] — tokens were not returned"
  FAILURES=$((FAILURES + 1))
  exit 1
fi

echo -e "\n   ${GREEN}access_token${NC}  → ${ACCESS_TOKEN:0:60}..."
echo -e "   ${GREEN}refresh_token${NC} → ${REFRESH_TOKEN:0:60}..."

# =============================================================================
# 5. LOGIN — invalid credentials
# =============================================================================
hdr "POST /auth/login — Invalid credentials (expects 401)"
run_test "login_bad_creds" 401 \
  -X POST "$BASE_URL/login" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: req-login-002" \
  -d '{"email":"john@example.com","password":"WrongPassword!"}' \

# =============================================================================
# 6. ME — valid token
# =============================================================================
hdr "GET /auth/me — Get user profile"
run_test "me_ok" 200 \
  -X GET "$BASE_URL/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Request-Id: req-me-001" \

# =============================================================================
# 7. ME — no token
# =============================================================================
hdr "GET /auth/me — No token (expects 401)"
run_test "me_no_token" 401 \
  -X GET "$BASE_URL/me" \
  -H "X-Request-Id: req-me-002" \

# =============================================================================
# 8. ME — malformed token
# =============================================================================
hdr "GET /auth/me — Invalid token (expects 401)"
run_test "me_bad_token" 401 \
  -X GET "$BASE_URL/me" \
  -H "Authorization: Bearer token.invalid.here" \
  -H "X-Request-Id: req-me-003" \

# =============================================================================
# 9. PATCH ME — actualizar nombre
# =============================================================================
hdr "PATCH /auth/me — Actualizar nombre"
run_test "update_me_name_ok" 200 \
  -X PATCH "$BASE_URL/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Request-Id: req-patchme-001" \
  -d '{"name":"John Patched"}'

# =============================================================================
# 10. PATCH ME — sin token (espera 401)
# =============================================================================
hdr "PATCH /auth/me — Sin token (espera 401)"
run_test "update_me_no_token" 401 \
  -X PATCH "$BASE_URL/me" \
  -H "Content-Type: application/json" \
  -H "X-Request-Id: req-patchme-002" \
  -d '{"name":"Hacker"}'

# =============================================================================
# 11. PATCH ME — contraseña vieja incorrecta (espera 400)
# =============================================================================
hdr "PATCH /auth/me — Contraseña vieja incorrecta (espera 400)"
run_test "update_me_wrong_password" 400 \
  -X PATCH "$BASE_URL/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Request-Id: req-patchme-003" \
  -d '{"old_password":"WrongOldPass!","new_password":"NewPass456!"}'

# =============================================================================
# 12. PATCH ME — cambio de contraseña correcto
# =============================================================================
hdr "PATCH /auth/me — Cambio de contraseña correcto"
run_test "update_me_password_ok" 200 \
  -X PATCH "$BASE_URL/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Request-Id: req-patchme-004" \
  -d '{"old_password":"SuperSecret123!","new_password":"NewPass456!"}'

# =============================================================================
# 13. REFRESH — renew access token
# =============================================================================
hdr "POST /auth/refresh — Renew access token"
dim "  → POST $BASE_URL/refresh"

REFRESH_BODY=$(mktemp)
REFRESH_STATUS=$(curl -s -o "$REFRESH_BODY" -w "%{http_code}" \
  -X POST "$BASE_URL/refresh" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Refresh-Token: $REFRESH_TOKEN" \
  -H "X-Request-Id: req-refresh-001")
REFRESH_RESPONSE=$(cat "$REFRESH_BODY"); rm -f "$REFRESH_BODY"

NEW_ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token' 2>/dev/null || true)

if [ -n "$NEW_ACCESS_TOKEN" ] && [ "$NEW_ACCESS_TOKEN" != "null" ]; then
  echo -e "${GREEN}✔ PASS${NC}  [refresh_ok]"
  echo -e "   ${GRAY}HTTP $REFRESH_STATUS (expected 200)${NC}"
  ACCESS_TOKEN="$NEW_ACCESS_TOKEN"
  echo -e "   ${GREEN}new access_token${NC} → ${ACCESS_TOKEN:0:60}..."
else
  echo -e "${RED}✘ FAIL${NC}  [refresh_ok]"
  echo -e "   ${RED}HTTP $REFRESH_STATUS — new access token not returned${NC}"
  FAILURES=$((FAILURES + 1))
fi

echo -e "   ${GRAY}Response:${NC}"
pretty "$REFRESH_RESPONSE" | sed 's/^/   /'

# =============================================================================
# 14. REFRESH — invalid refresh token
# =============================================================================
hdr "POST /auth/refresh — Invalid refresh token (expects 401)"
run_test "refresh_bad_token" 401 \
  -X POST "$BASE_URL/refresh" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Refresh-Token: refresh.token.invalid" \
  -H "X-Request-Id: req-refresh-002" \

# =============================================================================
# 15. LOGOUT
# =============================================================================
hdr "POST /auth/logout — Sign out"
run_test "logout_ok" 200 \
  -X POST "$BASE_URL/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Refresh-Token: $REFRESH_TOKEN" \
  -H "X-Request-Id: req-logout-001" \

# =============================================================================
# 16. ME — revoked token after logout
# =============================================================================
hdr "GET /auth/me — Revoked token after logout (expects 401)"
run_test "me_revoked" 401 \
  -X GET "$BASE_URL/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Request-Id: req-me-004" \

# =============================================================================
# 17. REFRESH — revoked tokens after logout
# =============================================================================
hdr "POST /auth/refresh — Revoked tokens after logout (expects 401)"
run_test "refresh_revoked" 401 \
  -X POST "$BASE_URL/refresh" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Refresh-Token: $REFRESH_TOKEN" \
  -H "X-Request-Id: req-refresh-003" \

# =============================================================================

# =============================================================================
# 18. UPDATE USER — PUT /auth/user/{user_id}
# =============================================================================
hdr "PUT /auth/user/{user_id} — Update user (no token)"

# Usar el usuario creado en signup_ok (John Doe). Obtener su id vía endpoint interno
USER_ID=""
USER_ID=$(curl -s -X GET "$BASE_URL/user/by-email/john@example.com" | jq -r '.id')

if [ -z "$USER_ID" ] || [ "$USER_ID" = "null" ]; then
  echo -e "${RED}✘ FAIL${NC}  [get_user_id] — could not get user id for update/delete tests"
  FAILURES=$((FAILURES + 1))
else
  run_test "update_user_ok" 200 \
    -X PUT "$BASE_URL/user/$USER_ID" \
    -H "Content-Type: application/json" \
    -d '{"name":"John Updated","email":"john.updated@example.com","password":"NewPass123!","role":"user"}'
fi

# =============================================================================
# 19. DELETE USER — DELETE /auth/user/{user_id}
# =============================================================================
hdr "DELETE /auth/user/{user_id} — Delete user (no token)"
if [ -z "$USER_ID" ] || [ "$USER_ID" = "null" ]; then
  echo -e "${RED}✘ FAIL${NC}  [get_user_id] — could not get user id for delete test"
  FAILURES=$((FAILURES + 1))
else
  run_test "delete_user_ok" 200 \
    -X DELETE "$BASE_URL/user/$USER_ID"
fi

# Summary
# =============================================================================
sep
TOTAL=19
PASSED=$((TOTAL - FAILURES))
echo -e "\n${YELLOW}Results:${NC} ${GREEN}${PASSED} passed${NC} · ${RED}${FAILURES} failed${NC} · ${TOTAL} total\n"

if [ "$FAILURES" -eq 0 ]; then
  echo -e "${GREEN}✔ All tests passed.${NC}\n"
  exit 0
else
  echo -e "${RED}✘ ${FAILURES} test(s) failed.${NC}\n"
  exit 1
fi