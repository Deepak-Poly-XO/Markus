from ddgs import DDGS

def search_web(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
        if not results:
            return "No results found."
        
        summary = ""
        for r in results:
            summary += f"{r['title']}: {r['body']}\n\n"
        return summary