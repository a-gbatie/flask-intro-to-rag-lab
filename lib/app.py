from __future__ import annotations

from flask import Flask, jsonify, request

from lib.ai_client import generate_response
from lib.company_documents import COMPANY_DOCUMENTS
from lib.rag_service import build_prompt, retrieve_context, source_metadata


def create_app():
  app = Flask(__name__)

  @app.get("/api/health")
  def health_check():
    return jsonify({"status": "ok"})

  @app.post("/api/ask")
  def ask_question():
    """Accept a query and return a source-backed generated answer.

    TODO:
    1. Read JSON request data safely.
    2. Validate that `query` is a non-empty string.
    3. Retrieve relevant context from COMPANY_DOCUMENTS.
    4. If no context is found, return a safe fallback with an empty sources list.
    5. Build a structured prompt from the selected context.
    6. Call generate_response(prompt).
    7. Return query, answer, and sources as JSON.
    8. If generate_response raises RuntimeError, return a 503 service error.
    """
    data = request.get_json(silent=True) or {} # reads JSON and converts to Python dict
    query = data.get("query") # retrieves user's question
    
    if not isinstance(query, str) or not query.strip(): # checks if query is a string and if there's text not just empty space
      return jsonify({"error": "Query must be a non-empty string."}), 400
    
    query = query.strip()
    context_matches = retrieve_context(query, COMPANY_DOCUMENTS) # connects Flask endpoint to retrieval function
    
    if not context_matches:
      return jsonify({
        "query": query,
        "answer": "I couldn't find relevant information in the company documents.",
        "sources": []
      }), 200
    
    prompt = build_prompt(query, context_matches) # build_prompt() takes in two arguements
    answer = generate_response(prompt) # takes prompt created, sends to Ollama, and returns AI answer
    sources = []
    
    for match in context_matches: # calls source_metadata() for every retrieved document and adds results to sources list
      sources.append(source_metadata(match))
      
    return jsonify({
      "query": query, 
      "answer": answer,
      "sources": sources
    }), 200
    
  return app


app = create_app()


if __name__ == "__main__":
  app.run(debug=True)
