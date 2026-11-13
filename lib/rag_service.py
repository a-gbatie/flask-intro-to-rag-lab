from __future__ import annotations

import re
from typing import Any

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "get",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "need",
    "of",
    "on",
    "or",
    "our",
    "should",
    "so",
    "the",
    "their",
    "to",
    "use",
    "what",
    "when",
    "where",
    "who",
    "why",
    "with",
    "you",
    "your",
}


def tokenize(text: str) -> set[str]:
  """Convert text into a set of searchable lowercase tokens.

  TODO:
  - Lowercase the text.
  - Extract word-like values.
  - Remove leading/trailing apostrophes.
  - Remove tokens with length <= 1.
  - Remove tokens in STOPWORDS.
  - Return a set of searchable terms.
  """
  text = text.lower() # converts to lowercase
  words = re.findall(r"[a-z0-9']+", text) # extract words
  tokens = set() # create empty set
  
  for word in words: # clean and filter words
    word = word.strip("")
    
    if len(word) > 1 and word not in STOPWORDS: # checks both conditions before adding to set
      tokens.add(word)

  return tokens # return set


def document_search_text(document: dict[str, Any]) -> str:
  """Combine searchable document fields into one text value.

  TODO:
  Include title, category, tags, and text.
  """
  title = document["title"]
  category = document["category"]
  tags = " ".join(document["tags"])
  content = document["text"]
  
  return f"{title} {category} {tags} {content}"


def score_document(query: str, document: dict[str, Any]) -> dict[str, Any]:
  """Score a document using keyword overlap.

  TODO:
  - Tokenize the query.
  - Tokenize the combined searchable document text.
  - Tokenize the document title.
  - Find matched terms between query tokens and document tokens.
  - Add a small title boost: 0.5 for each query token found in the title.
  - Return a dictionary with keys: document, score, matched_terms.
  """
  query_tokens = tokenize(query)
  document_tokens = tokenize(document_search_text(document))
  title_tokens = tokenize(document["title"])
  
  matched_terms = query_tokens & document_tokens
  score = len(matched_terms)
  
  title_matches = query_tokens & title_tokens
  score += 0.5 * len(title_matches)
  
  return {
    "document": document,
    "score": score,
    "matched_terms": sorted(matched_terms),
  }


def retrieve_context(
    query: str,
    documents: list[dict[str, Any]],
    limit: int = 2,
    minimum_score: float = 1.0,
) -> list[dict[str, Any]]:
    """Select the most relevant documents for the query.

    TODO:
    - Score all documents.
    - Keep only matches with score >= minimum_score.
    - Sort by score from highest to lowest.
    - Return only the top `limit` matches.

    The selected context must depend on the user's query. Do not return the same
    hardcoded document for every request.
    """
    scored_documents = [] # create empty list
    
    for document in documents: # loop throught every document
      result = score_document(query, document) # calculate document's score
      scored_documents.append(result) # save result
    
    relevant_documents = []
    
    for result in scored_documents:
      if result["score"] >= minimum_score:
        relevant_documents.append(result)
    
    relevant_documents.sort(
      key=lambda result: result["score"],
      reverse=True
    )
    return relevant_documents[:limit]
        

def format_context(context_matches: list[dict[str, Any]]) -> str:
    """Format retrieved documents into a context block for the prompt.

    TODO:
    - If no matches exist, return a short no-context message.
    - For each match, include Source ID, Title, Category, and Content.
    - Separate document blocks clearly.
    """
    if not context_matches: # no matching documents
      return "No relevant context found." 
    
    context_blocks = [] # empty list to store formatted text
    
    for match in context_matches:
      document = match["document"]
      block = (
        f"Source ID: {document['id']}\n"
        f"Title: {document['title']}\n"
        f"Category: {document['category']}\n"
        f"Content: {document['text']}\n"
      )
      
      context_blocks.append(block)
    return "\n\n".join(context_blocks)


def build_prompt(query: str, context_matches: list[dict[str, Any]]) -> str:
    """Build a structured prompt with instructions, context, question, and requirements.

    TODO:
    The prompt should include these sections:
    - Instructions
    - Context
    - Question
    - Response requirements

    The prompt should tell the model to use only the provided context and avoid
    inventing unsupported details.
    """
    context = format_context(context_matches) # converts documents into readable text
    instructions = (
      "Instructions:\n"
      "You are a helpful company assistant.\n"
      "Answer the user's question using only the provided context.\n"
      "Do not invent information that is not supported by the context."
    )
    
    prompt = (
      f"{instructions}\n\n"
      f"Context:\n{context}\n\n"
      f"Question:\n{query}\n\n"
      "Response requirements:\n"
      "Provide a clear and concise answer.\n"
      "Use only information supported by the context.\n"
      "If the context does not contain the answer, say you don't know."
    )
    
    return prompt


def source_metadata(match: dict[str, Any]) -> dict[str, str]:
    """Return source information that is safe to expose in the API response.

    TODO:
    Return only the document id and title.
    """
    document = match["document"]
    return {
      "id": document["id"],
      "title": document["title"]
    }
