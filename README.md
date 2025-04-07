# Neo4j MCP Chainlit

A proof of concept demonstrating integration between Neo4j MCP server with Chainlit (MCP host) and Claude LLM (Anthropic API).

## Overview

This project creates an interactive chat interface to query Neo4j databases using natural language. It leverages:

- Chainlit for the web interface
- Neo4j's MCP (Model Context Protocol) for database access
- Claude from Anthropic as the LLM for natural language understanding

## Quick Start Guide

### Prerequisites

1. Clone the repository:

```bash
git clone https://github.com/Abhid14/neo4j-mcp-chainlit.git
cd neo4j-mcp-chainlit
```

2. Install `uv` on your system:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For additional installation options, check the [uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

### Setup

1. Create a Python virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
uv pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
```

4. Add your Anthropic API key to the `.env` file:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### Running the Application

Start the Chainlit app:

```bash
chainlit run app.py -w
```

### Configure MCP Connections

1. In the Chainlit app interface, configure MCP connections
2. Use the sample Neo4j database:
   - Set the MCP connection in stdio mode
   - Name it `neo4j-mcp-demo`
   - Set the Command to:
     ```
     /path/to/uv/binary/uvx mcp-neo4j-cypher --db-url neo4j+s://demo.neo4jlabs.com --user recommendations --password recommendations
     ```

## Demo

The application uses the Neo4j demo database (Movie Graph) to demonstrate natural language querying capabilities.

Try asking questions like:

- "What movies did Tom Hanks act in?"
- "Show me the relationship between actors and directors"
- "Find all movies released after 2010"
