def buddy_respond(task):
    query = task.get("query", "") if task else ""
    return {
        "expert": "buddy",
        "message": f"Buddy received: {query}" if query else "Hey! What can I help you with?",
        "query": query,
    }
