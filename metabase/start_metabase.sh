#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Garante que o PostgreSQL esteja rodando no Docker
if [ ! "$(docker ps -q -f name=b3-postgres)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=b3-postgres)" ]; then
        echo "--> Iniciando container b3-postgres existente..."
        docker start b3-postgres
    else
        echo "--> Criando novo container b3-postgres..."
        docker run -d --name b3-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=b3 -p 5432:5432 postgres:16-alpine
    fi
else
    echo "--> Container b3-postgres já está em execução."
fi

# 2. Executa o Metabase na porta 3001
echo "--> Iniciando Metabase em http://localhost:3001 (Pressione Ctrl+C para parar)..."
cd "$DIR"
MB_JETTY_PORT=3001 java -jar metabase.jar

