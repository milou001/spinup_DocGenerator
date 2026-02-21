#!/bin/bash

# DocGenerator Production Startup Script

set -e

echo "🚀 DocGenerator - Starting up..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! command -v python3.13 &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

PYTHON_CMD=${PYTHON_CMD:-/home/linuxbrew/.linuxbrew/bin/python3.13}
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}✅ Python: $(${PYTHON_CMD} --version)${NC}"

# Initialize database
echo -e "${BLUE}🗄️  Initializing database...${NC}"
${PYTHON_CMD} scripts/init_db.py
echo -e "${GREEN}✅ Database ready${NC}"

# Check Ollama
echo -e "${BLUE}🧠 Checking Ollama...${NC}"
if curl -s http://openclaw-8ola-ollama-1:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is available${NC}"
else
    echo "⚠️  Warning: Ollama might not be accessible"
    echo "   Expected at: http://openclaw-8ola-ollama-1:11434"
fi

echo ""
echo -e "${BLUE}🚀 Starting FastAPI Server...${NC}"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Frontend: frontend/index.html"
echo ""

# Start server
${PYTHON_CMD} -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
