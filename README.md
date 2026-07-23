<div align="center">

# 🧠 DOCBOT 2.0

### Offline Intelligent Document Assistant

*Private • Local • AI-Powered*

<br>

![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=flat-square&logo=react&logoColor=black)
![LangChain](https://img.shields.io/badge/LangChain-Framework-1C3C3C?style=flat-square)
![Ollama](https://img.shields.io/badge/LLM-Ollama-000000?style=flat-square)
![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-7B3FE4?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

</div>

---

## ✦ What is DOCBOT?

**DOCBOT 2.0** is a privacy-first, offline **Retrieval-Augmented Generation (RAG)** assistant that allows you to upload documents and interact with them using a local Large Language Model.

Unlike cloud-based AI assistants, DOCBOT runs completely on your machine, ensuring **your documents never leave your device**.

---

## ✦ Features

- 📄 Intelligent Document Processing
- 💬 Context-Aware AI Chat
- 🔍 Semantic Search with ChromaDB
- 📷 OCR for Scanned PDFs
- 🧠 Interactive Knowledge Graph
- 📝 AI Summaries & Quiz Generation
- 📊 Analytics Dashboard
- 🔐 JWT Authentication
- 🐳 Fully Dockerized
- ⚡ Powered by Local LLMs using Ollama

---

## ✦ Tech Stack

| Layer | Technology |
|--------|------------|
| **Frontend** | React • TypeScript • Tailwind CSS |
| **Backend** | FastAPI • Python |
| **AI** | LangChain • Ollama • Llama 3 |
| **Vector Database** | ChromaDB |
| **Database** | SQLite |
| **Deployment** | Docker • Nginx • GitHub Actions |

---

## ✦ Quick Start

### Clone the repository

```bash
git clone https://github.com/mesasarah/DocbotV2.git
cd DocbotV2
```

### Start DOCBOT

```bash
./scripts/setup.sh
docker-compose up --build -d
./scripts/pull-model.sh
```

Open your browser at:

```text
http://localhost
```

---

## ✦ Architecture

```text
                Browser
                    │
                    ▼
           React + Nginx
                    │
               FastAPI API
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
   SQLite Database          ChromaDB
                                   │
                                   ▼
                           Ollama (Local LLM)
```

---

## ✦ Roadmap

- 🎙 Voice Conversations
- 📚 Multi-Document Comparison
- 🌍 Document Translation
- 👨‍💼 Admin Dashboard
- ✍ Offline Grammar Assistant

---

## ✦ Authors

**Mesa Sarah Vasantha Zephyr**

**Rampalli Prajna Paramita**

Developed from research carried out during an internship at **DRDO – Advanced Systems Laboratory, Hyderabad**.

---

<div align="center">

### 🔒 Built for Privacy • 🧠 Powered by AI • ⚡ Runs Completely Offline

⭐ **If you like this project, consider giving it a star!**

</div>