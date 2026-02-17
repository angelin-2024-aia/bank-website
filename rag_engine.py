import ollama
import os

# Global variable to store context in memory (Caching)
_cached_context = None

def load_context():
    global _cached_context
    if _cached_context is None:
        context = ""
        docs_path = "rag_docs"
        # Files-ai oru murai mattum read pannum
        if os.path.exists(docs_path):
            for filename in os.listdir(docs_path):
                file_path = os.path.join(docs_path, filename)
                if os.path.isfile(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        context += f.read() + "\n"
        _cached_context = context
    return _cached_context

def get_rag_response(question):
    # Memory-la irundhu context-ai fast-ah edukkum
    context = load_context()

    # Ollama llama3.2 model call
    # "You are an STB Bank Assistant" nu context add panni irukkaen bank related-ah badhil solla
    prompt = f"System: You are an STB Bank AI Assistant. Answer based ONLY on context.\nContext: {context}\n\nQuestion: {question}\n\nAnswer:"
    
    try:
        response = ollama.generate(model='llama3.2', prompt=prompt)
        return response['response']
    except Exception as e:
        return f"Error: {str(e)}"