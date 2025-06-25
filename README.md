# SportChatbot

## Project Overview

This project implements a RAG (Retrieval-Augmented Generation) system that combines document retrieval with generative
AI to provide accurate, context-aware responses. 

## Key Technologies

### Core Components

- **MongoDB**: Document database for storing scraped articles and metadata
- **Vector Database (ChromaDB)**: For storing and retrieving embeddings
- **OpenAI GPT-4**: For generating responses and embeddings
- **Flask**: Backend REST API framework
- **Streamlit**: Frontend interface

### Important Libraries

- `langchain`: For RAG implementation and embeddings management
- `openai`: OpenAI API integration
- `pymongo`: MongoDB client
- `flask`: Web framework for the backend API
- `chromadb`: Vector database for similarity search
- `requests`: HTTP client for API communication

## System Architecture

The system consists of several microservices:

1. **Scraper Service**
    - Responsible for collecting and processing source documents
    - Stores documents in MongoDB

2. **RAG Updater Service**
    - Processes documents and generates embeddings
    - Updates the vector store with new embeddings
    - Maintains the ChromaDB vector database

3. **Backend Service**
    - Provides REST API endpoints
    - Handles query processing and RAG operations
    - Integrates with OpenAI for response generation
    - Manages vector store retrieval

4. **Frontend Service**
    - User interface for interacting with the system
    - Displays query results and sources
    - Handles user input and visualization

5. **MongoDB Service**
    - Persistent storage for documents and metadata
    - Maintains data consistency across services

## Running the Project

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

### Setup and Deployment

1. Clone the repository

2. Create a `.env` file in the project root with: OPENAI_API_KEY=your_openai_api_key_here
3. Run the entire stack using Docker Compose:

```bash
docker compose up -d
```

This will start all services:

- Frontend will be available at `http://localhost:8501`
- Backend API at `http://localhost:8000`
- MongoDB at `localhost:27017`

### Service Dependencies

- Frontend depends on Backend
- Backend depends on MongoDB and vector store
- RAG Updater depends on MongoDB
- Scraper depends on MongoDB

### Persistent Storage

The system uses Docker volumes for persistent storage:

- : For MongoDB documents `mongodb_data`
- : For ChromaDB vector store `vectorstore_data`

## Architecture Design
<img width="388" alt="Image" src="https://github.com/user-attachments/assets/ef834bf1-2a88-4b30-838c-ffce10409ab2" />
