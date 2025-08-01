# Payment Processor API - Rinha de Backend

API para processamento de pagamentos desenvolvida para a Rinha de Backend, utilizando FastAPI, Celery, Redis, PostgreSQL e Nginx como load balancer.

## 📋 Visão Geral

Este projeto implementa uma API de processamento de pagamentos com arquitetura distribuída, utilizando:

- **FastAPI**: Framework web moderno e rápido para Python
- **Celery**: Sistema de filas distribuído para processamento assíncrono
- **Redis**: Cache e message broker para Celery
- **PostgreSQL**: Banco de dados relacional principal
- **Nginx**: Load balancer e proxy reverso
- **Docker**: Containerização de todos os serviços

## 🏗️ Arquitetura

O sistema é composto por múltiplos containers que trabalham em conjunto:

- **2 instâncias da API** (api, api2): Para alta disponibilidade
- **1 Worker Celery**: Para processamento assíncrono de pagamentos
- **Nginx**: Load balancer entre as instâncias da API
- **Redis**: Message broker e cache
- **PostgreSQL**: Banco de dados principal
- **Payment Processors**: Serviços externos para processamento (default e fallback)

## 🚀 Funcionalidades

### Endpoints Principais

- `POST /payments`: Recebe solicitações de pagamento para processamento assíncrono
- `GET /payments-summary`: Retorna resumo de pagamentos com filtros opcionais de data
- `POST /payments-purge`: Limpa todos os dados de pagamentos do banco

## 📊 Especificações dos Containers

| Container | CPU (cores) | Memória (MB) | Imagem | Função |
|-----------|-------------|--------------|---------|---------|
| **api** | 0.31 | 89 | Custom Build | API Principal |
| **api2** | 0.31 | 89 | Custom Build | API Secundária |
| **worker** | 0.31 | 98 | Custom Build | Worker Celery |
| **nginx** | 0.19 | 18 | nginx:latest | Load Balancer |
| **redis** | 0.19 | 24 | redis:8.0.3 | Cache/Message Broker |
| **postgres** | 0.19 | 34 | postgres:15.1 | Banco de Dados |

### **Total de Recursos**
- **CPU Total**: 1.50 cores
- **Memória Total**: 350 MB

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.13+**
- **FastAPI**: Framework web assíncrono
- **SQLAlchemy**: ORM para banco de dados
- **Pydantic**: Validação de dados
- **Celery**: Processamento assíncrono
- **HTTPX**: Cliente HTTP assíncrono

### Infraestrutura
- **Docker & Docker Compose**: Containerização
- **Nginx**: Load balancer e proxy reverso
- **Redis**: Cache e message broker
- **PostgreSQL**: Banco de dados relacional

## 🚀 Como Executar

### Pré-requisitos
- Docker
- Docker Compose

### Executando o Projeto

1. **Clone o repositório**
```bash
git clone "https://github.com/Juanlimalf/payment_processor-rinha_backend_2025.git"
cd payment-processor-rinha-backend
```

2. **Inicie os processadores de pagamento**
```bash
cd payment-processor
docker-compose up -d
cd ..
```

3. **Inicie a aplicação principal**
```bash
docker-compose up -d
```

4. **Verifique se todos os serviços estão rodando**
```bash
docker-compose ps
```

### Acessando a Aplicação

- **API Principal**: http://localhost:9999
- **Banco PostgreSQL**: localhost:5432

## 📝 Configurações

### Variáveis de Ambiente

- `REDIS_URL`: URL de conexão com Redis
- `DATABASE_URL`: URL de conexão com PostgreSQL
- `PAYMENT_PROCESSOR_DEFAULT`: URL do processador principal
- `PAYMENT_PROCESSOR_FALLBACK`: URL do processador fallback


## 👨‍💻 Autor

**Juan Lima** - [juanlimalf@gmail.com](mailto:juanlimalf@gmail.com)

**linkdIn** - [https://www.linkedin.com/in/juanlimalf/](https://www.linkedin.com/in/juanlimalf/)