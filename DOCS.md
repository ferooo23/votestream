# VoteStream API Documentation

## Core Endpoints

### Health & Monitoring
- `GET /health` - System health check
- `GET /stats` - Basic application statistics
- `GET /metrics` - Advanced performance metrics

### Polls Management
- `GET /polls` - List all polls
- `POST /polls` - Create new poll
- `GET /polls/{id}` - Get specific poll
- `POST /polls/{id}/vote` - Submit vote
- `GET /polls/{id}/results` - Get poll results

### Themes
- `GET /themes` - Get available themes
- `GET /themes/{theme}/polls` - Get polls by theme

### Real-time
- `WS /polls/{id}/stream` - WebSocket for real-time updates

## Request/Response Examples

### Create Poll
```bash
curl -X POST http://localhost/polls \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your favorite programming language?",
    "theme": "OnTrend",
    "options": [
      {"text": "Python"},
      {"text": "JavaScript"},
      {"text": "Go"},
      {"text": "Rust"}
    ]
  }'
```

### Vote
```bash
curl -X POST http://localhost/polls/1/vote \
  -H "Content-Type: application/json" \
  -d '{"choice": 0}'
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost/polls/1/stream');
ws.onmessage = (event) => {
  const results = JSON.parse(event.data);
  console.log('Live results:', results);
};
```

## Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │────│    Nginx    │────│   FastAPI   │
│  (Browser)  │    │Load Balancer│    │   App x3    │
└─────────────┘    └─────────────┘    └─────────────┘
                          │                    │
                          │            ┌─────────────┐
                          │            │ PostgreSQL  │
                          │            │  Database   │
                          │            └─────────────┘
                          │                    │
                          │            ┌─────────────┐
                          └────────────│    Redis    │
                                       │Cache+PubSub │
                                       └─────────────┘
```

## Scalability Features

### State Management
- **PostgreSQL**: Persistent data storage
- **Redis**: Caching and pub/sub messaging
- **In-memory**: WebSocket connection tracking

### Horizontal Scaling
- Stateless application design
- Load balancing with Nginx
- Redis pub/sub for inter-instance communication

### Vertical Scaling
- Database connection pooling
- Redis connection pooling
- Configurable worker processes

### Protection Mechanisms
- Rate limiting (100 requests/minute per IP)
- Database connection limits
- Circuit breaker patterns
- Health checks and monitoring
