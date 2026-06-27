#!/usr/bin/env bash
# Foretell 本地开发：安装依赖并启动后端 + 前端
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BACKEND_PID=""
FRONTEND_PID=""

log() { printf '\033[1;34m[foretell]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[foretell]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[foretell]\033[0m %s\n' "$*" >&2; }

cleanup() {
  local code=$?
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    log "停止前端 (pid $FRONTEND_PID)..."
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    log "停止后端 (pid $BACKEND_PID)..."
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  exit "$code"
}
trap cleanup EXIT INT TERM

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "未找到命令: $1"
    case "$1" in
      uv)
        err "安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        ;;
      node)
        err "请先安装 Node.js 20+ (https://nodejs.org 或 nvm)"
        ;;
      pnpm)
        err "安装 pnpm: corepack enable && corepack prepare pnpm@latest --activate"
        ;;
    esac
    exit 1
  fi
}

ensure_pnpm() {
  if command -v pnpm >/dev/null 2>&1; then
    return
  fi
  if command -v corepack >/dev/null 2>&1; then
    log "启用 corepack 以使用 pnpm..."
    corepack enable >/dev/null 2>&1 || true
    corepack prepare pnpm@latest --activate >/dev/null 2>&1 || true
  fi
  require_cmd pnpm
}

load_api_endpoint() {
  API_HOST="127.0.0.1"
  API_PORT="8000"
  if [[ -f "$ROOT/.env" ]]; then
    # shellcheck disable=SC1091
    set -a
    source "$ROOT/.env"
    set +a
  fi
  API_HOST="${API_HOST:-127.0.0.1}"
  API_PORT="${API_PORT:-8000}"
}

wait_for_backend() {
  local url="http://${API_HOST}:${API_PORT}/health"
  log "等待后端就绪: $url"
  for _ in $(seq 1 60); do
    if curl -sf "$url" >/dev/null 2>&1; then
      log "后端已就绪"
      return 0
    fi
    if [[ -n "$BACKEND_PID" ]] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
      err "后端进程已退出，请检查上方日志"
      return 1
    fi
    sleep 1
  done
  err "后端启动超时（60s）"
  return 1
}

# --- 依赖检查 ---
require_cmd uv
require_cmd node
ensure_pnpm

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [[ "$NODE_MAJOR" -lt 20 ]]; then
  warn "建议使用 Node.js 20+，当前: $(node -v)"
fi

# --- Python 环境 ---
log "安装 Python 3.14 并同步后端依赖..."
uv python install 3.14
uv sync

# --- 环境变量文件 ---
if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  warn "已创建 .env，请填入 MINIMAX_API_KEY 与 MYSQL_* 等配置后重新运行"
fi

if [[ ! -f "$ROOT/frontend/.env.local" ]]; then
  cp "$ROOT/frontend/.env.local.example" "$ROOT/frontend/.env.local"
  log "已创建 frontend/.env.local"
fi

if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  if [[ "${MINIMAX_API_KEY:-}" == "your-minimax-api-key" || -z "${MINIMAX_API_KEY:-}" ]]; then
    warn "MINIMAX_API_KEY 未配置，对话功能可能不可用"
  fi
fi

# --- 前端依赖 ---
log "安装前端依赖..."
(
  cd "$ROOT/frontend"
  pnpm install --frozen-lockfile
  # pnpm 11+ 默认拦截 lifecycle scripts，需批准 sharp 等原生依赖
  if pnpm approve-builds --help >/dev/null 2>&1; then
    pnpm approve-builds --all >/dev/null 2>&1 || true
    pnpm install --frozen-lockfile
  fi
)

load_api_endpoint

# --- 启动服务 ---
log "启动后端: uvicorn api.main:app --reload --host $API_HOST --port $API_PORT"
uv run uvicorn api.main:app --reload --host "$API_HOST" --port "$API_PORT" &
BACKEND_PID=$!

wait_for_backend

log "启动前端: pnpm dev (http://localhost:3000)"
(cd "$ROOT/frontend" && pnpm dev) &
FRONTEND_PID=$!

echo
log "开发环境已就绪"
log "  前端: http://localhost:3000"
log "  后端: http://${API_HOST}:${API_PORT}"
log "  健康检查: http://${API_HOST}:${API_PORT}/health"
log "按 Ctrl+C 停止前后端"
echo

# 任一子进程退出则结束（兼容 macOS 自带 bash 3.2）
while kill -0 "$BACKEND_PID" 2>/dev/null || kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done
wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
