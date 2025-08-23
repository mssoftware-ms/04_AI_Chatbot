# LiteLLM Integration Guide for Claude Code

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Basic Setup](#basic-setup)
- [Production Setup](#production-setup)
- [Model Configuration](#model-configuration)
- [Multi-Tenant Configuration](#multi-tenant-configuration)
- [Testing & Validation](#testing--validation)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

## Overview

LiteLLM acts as a universal LLM gateway that enables Claude Code to route requests to multiple non-Anthropic models while maintaining the same interface. This integration provides cost optimization, fallback capabilities, and multi-tenant support for enterprise deployments.

### Key Benefits

- **Multi-Provider Support**: Route to OpenAI, Azure, OpenRouter, Bedrock, Ollama, and 100+ providers
- **Cost Optimization**: Automatically use cheaper models for appropriate tasks
- **High Availability**: Fallback chains ensure resilience
- **Multi-Tenancy**: Isolated configurations and budgets per team
- **Enterprise Features**: Monitoring, audit logging, and compliance

## Quick Start

### Minimal Setup (5 minutes)

```bash
# 1. Navigate to examples directory
cd /examples/litellm

# 2. Start basic LiteLLM proxy
docker-compose -f docker-compose.basic.yml up -d

# 3. Configure Claude Code
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_AUTH_TOKEN=sk-1234567890

# 4. Test with Claude Code
claude --model test-model "Hello, world!"
```

### Verify Installation

```bash
# Check health
curl -s http://localhost:4000/health \
  -H "Authorization: Bearer sk-1234567890" | jq .

# List available models
curl -s http://localhost:4000/models \
  -H "Authorization: Bearer sk-1234567890" | jq .
```

## Architecture

### Component Overview

```
┌──────────────┐      ┌──────────────┐      ┌─────────────────┐
│ Claude Code  │─────▶│   LiteLLM    │─────▶│  LLM Providers  │
│   Clients    │      │    Proxy     │      │  (OpenAI, etc)  │
└──────────────┘      └──────────────┘      └─────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼────┐    ┌──────▼──────┐
              │   Redis  │    │  PostgreSQL │
              │  Cache   │    │   Database  │
              └──────────┘    └─────────────┘
```

### Request Flow

1. Claude Code sends request to LiteLLM endpoint
2. LiteLLM authenticates and validates the request
3. Router selects appropriate model based on configuration
4. Request forwarded to selected provider
5. Response streamed back to Claude Code
6. Usage tracked and logged

## Basic Setup

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- API keys for desired providers

### Step 1: Create Configuration

Create `config/basic-config.yaml`:

```yaml
model_list:
  # OpenAI Models
  - model_name: "gpt-4o-mini"
    litellm_params:
      model: "openai/gpt-4o-mini"
      api_key: ${OPENAI_API_KEY}
      
  # OpenRouter Models  
  - model_name: "qwen-coder"
    litellm_params:
      model: "openrouter/qwen/qwen-3-coder"
      api_key: ${OPENROUTER_API_KEY}
      
  # Local Models (Ollama)
  - model_name: "local-codellama"
    litellm_params:
      model: "ollama/codellama"
      api_base: http://localhost:11434

general_settings:
  master_key: ${LITELLM_MASTER_KEY}
  request_timeout: 600
```

### Step 2: Set Environment Variables

Create `.env` file:

```bash
LITELLM_MASTER_KEY=sk-your-secure-key
OPENAI_API_KEY=sk-your-openai-key
OPENROUTER_API_KEY=sk-or-your-openrouter-key
```

### Step 3: Launch Services

```bash
docker-compose -f docker-compose.basic.yml up -d
```

### Step 4: Configure Claude Code

Add to your shell profile:

```bash
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_AUTH_TOKEN=sk-your-secure-key
```

## Production Setup

### Full Stack Deployment

```bash
# 1. Clone and navigate
git clone https://github.com/ruvnet/claude-flow.git
cd claude-flow/examples/litellm

# 2. Configure environment
cp .env.example .env
# Edit .env with your keys

# 3. Deploy full stack
./scripts/deploy.sh start
```

### Production Components

- **3x LiteLLM Proxies**: Load-balanced for HA
- **Nginx Load Balancer**: Traffic distribution
- **PostgreSQL**: Configuration storage
- **Redis**: Response caching
- **Prometheus + Grafana**: Monitoring
- **Loki**: Log aggregation

### Docker Compose Services

```yaml
services:
  nginx:          # Load balancer on port 4000
  litellm-1/2/3:  # Proxy instances
  postgres:       # Database on port 5432
  redis:          # Cache on port 6379
  prometheus:     # Metrics on port 9090
  grafana:        # Dashboards on port 3000
  loki:           # Logs on port 3100
```

## Model Configuration

### Model Aliasing

Map Claude Code model names to providers:

```yaml
model_list:
  # Map Claude's model name to Qwen
  - model_name: "claude-3-5-sonnet"
    litellm_params:
      model: "openrouter/qwen/qwen-3-coder"
      max_tokens: 65536
      
  # Map to OpenAI
  - model_name: "claude-3-opus"
    litellm_params:
      model: "openai/gpt-4-turbo"
      max_tokens: 8192
```

### Fallback Chains

Configure automatic fallbacks:

```yaml
fallback_models:
  code_chain:
    - gpt-4o-mini      # Fast, cheap
    - qwen-coder       # Alternative
    - local-codellama  # Local fallback
    
  reasoning_chain:
    - gpt-4-turbo      # Primary
    - claude-3-opus    # Fallback
```

### Cost Optimization

```yaml
model_list:
  - model_name: "cheap-code"
    litellm_params:
      model: "openrouter/deepseek/deepseek-coder"
    model_info:
      cost_per_token: 0.000001  # Very cheap
      
  - model_name: "premium-reasoning"
    litellm_params:
      model: "openai/o3-pro"
    model_info:
      cost_per_token: 0.00015   # Expensive
```

## Multi-Tenant Configuration

### Create Tenant

```bash
./scripts/manage-tenants.sh create engineering \
  sk-eng-key \
  100 \
  "gpt-4o-mini,qwen-coder"
```

### Tenant Configuration File

`tenants/engineering.yaml`:

```yaml
tenant:
  id: engineering
  api_key: sk-eng-secure-key
  
allowed_models:
  - gpt-4o-mini
  - qwen-coder
  - local-codellama
  
budget:
  daily_limit: 100
  monthly_limit: 3000
  
rate_limits:
  requests_per_minute: 60
  requests_per_hour: 1000
```

### Usage by Tenant

```bash
# Engineering team
export ANTHROPIC_AUTH_TOKEN=sk-eng-secure-key
claude --model gpt-4o-mini "Build feature"

# Research team  
export ANTHROPIC_AUTH_TOKEN=sk-research-key
claude --model gpt-4-turbo "Analyze data"
```

## Testing & Validation

### Health Check

```bash
curl -X GET http://localhost:4000/health \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

Expected response:
```json
{
  "healthy_endpoints": [...],
  "healthy_count": 2,
  "unhealthy_count": 0
}
```

### List Models

```bash
curl -X GET http://localhost:4000/models \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

### Test Chat Completion

```bash
curl -X POST http://localhost:4000/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### Performance Test

```bash
# Concurrent requests test
for i in {1..10}; do
  curl -X POST http://localhost:4000/chat/completions \
    -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d '{"model": "test-model", "messages": [{"role": "user", "content": "Test"}]}' &
done
wait
```

## Troubleshooting

### Common Issues

#### 1. Authentication Error

**Problem**: `401 Authentication Error`

**Solution**:
```bash
# Check master key in .env
grep LITELLM_MASTER_KEY .env

# Verify in docker-compose.yml
docker-compose exec litellm env | grep MASTER_KEY
```

#### 2. Model Not Found

**Problem**: `Model not found`

**Solution**:
```bash
# List available models
curl http://localhost:4000/models \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"

# Check config
docker-compose exec litellm cat /app/config.yaml
```

#### 3. Connection Refused

**Problem**: Cannot connect to LiteLLM

**Solution**:
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs litellm

# Restart services
docker-compose restart
```

#### 4. Slow Response Times

**Problem**: High latency

**Solution**:
```yaml
# Enable caching in config.yaml
general_settings:
  cache_enabled: true
  cache_ttl: 3600
  
# Add Redis for caching
services:
  redis:
    image: redis:7-alpine
```

#### 5. Rate Limiting

**Problem**: `429 Too Many Requests`

**Solution**:
```yaml
# Adjust rate limits
rate_limits:
  requests_per_minute: 100
  requests_per_hour: 5000
```

### Debug Mode

Enable verbose logging:

```yaml
# docker-compose.yml
environment:
  - LITELLM_LOG_LEVEL=DEBUG
  - LITELLM_SET_VERBOSE=true
```

View debug logs:
```bash
docker-compose logs -f litellm | grep DEBUG
```

### Container Management

```bash
# Stop services
docker-compose down

# Remove volumes (caution: deletes data)
docker-compose down -v

# Rebuild containers
docker-compose build --no-cache

# Scale proxies
docker-compose up -d --scale litellm=5
```

## Advanced Topics

### Custom Providers

Add custom LLM providers:

```yaml
model_list:
  - model_name: "custom-llm"
    litellm_params:
      model: "custom_provider/model"
      api_base: "https://api.custom.com"
      api_key: ${CUSTOM_API_KEY}
      custom_llm_provider: "custom"
      extra_headers:
        X-Custom-Header: "value"
```

### SSL/TLS Configuration

Enable HTTPS:

```yaml
# nginx.conf
server {
  listen 443 ssl;
  ssl_certificate /certs/cert.pem;
  ssl_certificate_key /certs/key.pem;
}
```

### Monitoring Setup

Access dashboards:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

Key metrics to monitor:
- Request latency (p50, p95, p99)
- Token usage per model
- Error rates
- Cost per tenant

### Backup & Recovery

```bash
# Backup database
docker-compose exec postgres \
  pg_dump -U litellm > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T postgres \
  psql -U litellm < backup_20250807.sql

# Backup configuration
tar -czf config_backup.tar.gz config/ tenants/
```

### Performance Tuning

```yaml
# Optimize for high throughput
router_settings:
  max_parallel_requests: 100
  request_timeout: 30
  enable_caching: true
  
# Worker configuration
environment:
  - MAX_WORKERS=8
  - WORKER_TIMEOUT=300
```

### Security Best Practices

1. **Rotate API Keys**:
```bash
./scripts/rotate-keys.sh
```

2. **Network Isolation**:
```yaml
networks:
  internal:
    internal: true
  external:
    external: true
```

3. **Rate Limiting**:
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

## Integration Examples

### With Claude Code CLI

```bash
# Basic usage
claude --model gpt-4o-mini "Write a function"

# Streaming
claude --model qwen-coder --stream "Explain this code"

# With context
claude --model local-codellama --context file.py "Refactor this"
```

### Programmatic Usage

```python
import os
import requests

# Configure
os.environ['ANTHROPIC_BASE_URL'] = 'http://localhost:4000'
headers = {'Authorization': f'Bearer {os.environ["LITELLM_MASTER_KEY"]}'}

# Make request
response = requests.post(
    f"{os.environ['ANTHROPIC_BASE_URL']}/chat/completions",
    headers=headers,
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
```

## Resources

- [LiteLLM Documentation](https://docs.litellm.ai)
- [Claude Code Guide](https://docs.anthropic.com/en/docs/claude-code)
- [OpenRouter Models](https://openrouter.ai/models)
- [Example Configurations](https://github.com/ruvnet/claude-flow/tree/main/examples/litellm)

## Support

- **Issues**: [GitHub Issues](https://github.com/ruvnet/claude-flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ruvnet/claude-flow/discussions)
- **Wiki**: [Claude Flow Wiki](https://github.com/ruvnet/claude-flow/wiki)