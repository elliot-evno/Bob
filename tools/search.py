from duckduckgo_search import DDGS

def perform_search(query, num_results=3):
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=num_results))
    return results