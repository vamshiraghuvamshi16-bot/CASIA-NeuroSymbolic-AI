# app/web_search.py
import requests
from app.config import TAVILY_API_KEY

def web_search(query: str, max_results: int = 5) -> str:
    """
    Performs a web search using Tavily API and returns concatenated results.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to fetch.
    
    Returns:
        str: Concatenated search results.
    """
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "max_results": max_results
            },
            timeout=10
        )
        response.raise_for_status()  # Raises HTTPError if status != 200
        res_json = response.json()
        results = res_json.get("results", [])
        if not results:
            return "No results found."
        # Join content of results
        return "\n\n".join([f"{i+1}. {r.get('content','')}" for i, r in enumerate(results)])
    except requests.exceptions.RequestException as e:
        print("[web_search error] Request failed:", e)
        return ""
    except Exception as e:
        print("[web_search error]", e)
        return ""


# ----------------- Test / Debug -----------------
if __name__ == "__main__":
    test_query = "Python FAISS tutorial"
    output = web_search(test_query, max_results=5)
    print("=== Web Search Output (first 500 chars) ===")
    print(output[:500])
