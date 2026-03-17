FROM python:3.11

# 安装 Node.js （满足 >=18）及必要工具
# Install Node.js (>=18) and tools
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
  && apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# 通过 pip 安装 uv（替代直接拉取 ghcr.io 官方镜像，避免国内网络卡顿）
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ uv

# Copy uv from official image
# Install Node.js (>=18) and required tooling
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# Copy `uv` from the official image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for cache
# Copy dependency manifests first to maximize layer caching
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# 安装依赖（Node + Python），配置国内加速源
# Install dependencies (Node + Python)
RUN npm config set registry https://registry.npmmirror.com \
  && npm ci \
# Install dependencies (Node + Python)
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && env UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ uv sync --frozen

# Copy project source
# Copy project sources
COPY . .

EXPOSE 3000 5001

# Start frontend and backend (dev mode)
# Start frontend and backend together (development mode)
CMD ["npm", "run", "dev"]
