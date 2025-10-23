"""
# Requirements Management System

A modular requirements management system using LangGraph, FastAPI, and Neo4j.

## Features

- 🔑 Keyword generation from requirement descriptions
- 📝 Automated requirements generation
- ⚠️ Risk analysis for each requirement
- 🔄 Regeneration capability for requirements and risks
- 💾 Neo4j graph database integration
- 🚀 FastAPI REST API
- 📊 Comprehensive logging
- ✅ Full test coverage

## Project Structure

```
requirements_management/
├── __init__.py
├── config.py          # Configuration management
├── models.py          # Pydantic models
├── tools.py           # LangGraph tools for Neo4j
├── nodes.py           # LangGraph workflow nodes
├── graph.py           # Workflow graph definition
├── api.py             # FastAPI application
├── logger.py          # Logging configuration
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
├── README.md          # This file
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_tools.py
    ├── test_nodes.py
    └── test_api.py
```

## Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. Start Neo4j database (Docker):
   ```bash
   docker run -d \\
     --name neo4j \\
     -p 7474:7474 -p 7687:7687 \\
     -e NEO4J_AUTH=neo4j/12345678 \\
     neo4j:latest
   ```

## Usage

### Running the API

```bash
python api.py
```

Or with uvicorn:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Access the API documentation at: http://localhost:8000/docs

### API Endpoints

#### 1. Create Project
```bash
POST /project/create
{
  "requirement_description": "The benefits of adopting LangGraph",
  "project_name": "LangGraph_Project"
}
```

Response:
```json
{
  "thread_id": "LangGraph_Project",
  "status": "keywords_generated",
  "keywords": ["keyword one", "keyword two", ...]
}
```

#### 2. Select Keyword
```bash
POST /project/select-keyword
{
  "thread_id": "LangGraph_Project",
  "keyword_index": 0
}
```

#### 3. Regenerate Requirements/Risks
```bash
POST /project/regenerate
{
  "thread_id": "LangGraph_Project",
  "regenerate_type": "requirements"  # or "risks" or "both"
}
```

#### 4. Save to Neo4j
```bash
POST /project/save?thread_id=LangGraph_Project
```

#### 5. Get Project Status
```bash
GET /project/{thread_id}
```

#### 6. List All Projects
```bash
GET /projects
```

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_api.py -v
```

## Workflow

1. **Create Project**: Submit a requirement description
2. **Review Keywords**: System generates 5 keywords (3 words each)
3. **Select Keyword**: Choose one keyword to proceed
4. **Generate Requirements**: System creates 5 formal requirements
5. **Generate Risks**: System analyzes risks for each requirement
6. **Regenerate** (Optional): Regenerate requirements or risks
7. **Save**: Persist to Neo4j database

## Logging

Logs are written to:
- Console (colored output)
- File: `requirements_management.log`

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Neo4j Graph Structure

```
(Project)-[:HAS_REQUIREMENT]->(Requirement)-[:HAS_RISK]->(Risk)
       \\                                                    /
        \\------------------[:HAS_RISK]-------------------/
```

## Example Usage

```python
import requests

# 1. Create project
response = requests.post("http://localhost:8000/project/create", json={
    "requirement_description": "Build a scalable microservices architecture",
    "project_name": "Microservices_2025"
})
thread_id = response.json()["thread_id"]
keywords = response.json()["keywords"]

# 2. Select keyword
response = requests.post("http://localhost:8000/project/select-keyword", json={
    "thread_id": thread_id,
    "keyword_index": 0
})

# 3. Regenerate if needed
response = requests.post("http://localhost:8000/project/regenerate", json={
    "thread_id": thread_id,
    "regenerate_type": "requirements"
})

# 4. Save to database
response = requests.post(f"http://localhost:8000/project/save?thread_id={thread_id}")
```

## Development

### Adding New Nodes

1. Define node function in `nodes.py`
2. Add node to graph in `graph.py`
3. Create tests in `tests/test_nodes.py`

### Adding New Tools

1. Define tool in `tools.py` with `@tool` decorator
2. Add tool to ToolNode if needed
3. Create tests in `tests/test_tools.py`

### Adding New API Endpoints

1. Define endpoint in `api.py`
2. Add request/response models in `models.py`
3. Create tests in `tests/test_api.py`

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit pull request
"""