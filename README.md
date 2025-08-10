# 🤖 XoneBot - AI Cafe Automation System

XoneBot is a universal AI assistant that automates cafe operations by replacing waiters with intelligent conversation.

## 🚀 Features
- Multi-channel support (QR codes, voice calls, WhatsApp, website)
- Natural language order processing
- Multi-tenant architecture (one system, many cafes)
- Real-time order management
- AI-powered customer service

## 📋 Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/xonebot-backend
cd xonebot-backend


Building on Week 1's foundation, we'll add:
1. **Order Processing System** - Complete order lifecycle management
2. **Real-time WebSocket Updates** - Live order status and notifications
3. **Table Management with QR Codes** - Generate and manage QR codes for tables
4. **Chat Integration Structure** - Foundation for AI chat system


uvicorn app.main:app --reload --port 8000

ngrok http 8000