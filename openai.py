from openaiclient import client



def check_volume_request(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": """If the user wants to change the volume, return <Volume: 'up'> or <Volume: 'down'>.
Otherwise, return 'Not a volume request'."""},
            {"role": "user", "content": question}
        ]
    )
    content = response.choices[0].message.content.lower()
    if "<volume:" in content:
        direction = content.split("'")[1]
        return direction
    return None




def check_music_request(question):
    # Clean up the input text by adding spaces between merged words
    cleaned_question = ' '.join(''.join(' ' + char if char.isupper() else char for char in question).strip().split())
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": """Analyze the user's request and respond in one of these formats:
- If they want to play music (keywords like "play", "put on", "start"): <Play: '{artist or song}'>
- If they're asking about a song but describing it: <Search: '{description}'>
- If they want to stop music: <Stop>
- Otherwise: 'Not a music request'

Examples:
"PlayMichael Jackson" -> <Play: 'Michael Jackson'>
"play thriller" -> <Play: 'thriller Michael Jackson'>
"put on some queen" -> <Play: 'queen'>"""},
            {"role": "user", "content": cleaned_question}
        ]
    )
    content = response.choices[0].message.content.lower()
    
    if "<play:" in content:
        song = content.split("'")[1]
        return ("play", song)
    elif "<search:" in content:
        description = content.split("'")[1]
        return ("search", description)
    elif "<stop>" in content:
        return ("stop", None)
    return None




def summarize_search_results(question, results, current_time):
    context = "\n".join([f"Source: {r['href']}\nTitle: {r['title']}\nContent: {r['body']}" for r in results])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.15,
        max_tokens=150,  # Reduced token limit for shorter responses
        messages=[
            {"role": "system", "content": f"""The current time is {current_time}. You are an AI assistant designed to provide brief, direct answers. Your responses should be concise and to the point.




Instructions:
1. Provide a clear, concise answer to the user's question.
2. Include only the most relevant information.
3. Avoid unnecessary explanations or context unless directly asked.
4. Use simple language and short sentences.
5. If the question is time-sensitive, incorporate the current time in your answer.
6. Only mention sources if absolutely necessary for credibility.




Remember, your goal is to give a short, direct response that answers the user's question without any extra information."""},
            {"role": "user", "content": f"Question: {question}\n\nSearch Results:\n{context}"}
        ]
    )
    return response.choices[0].message.content.strip()


def check_timer_or_alarm(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": """If the user wants to set a timer, return <Timer: '{amount of seconds}'/>.
If the user wants to set an alarm, return <Alarm: '{time in HH:MM format}'/>.
Otherwise, return 'No timer or alarm'."""},
            {"role": "user", "content": question}
        ]
    )
    content = response.choices[0].message.content.lower()
    if "<timer:" in content:
        seconds = content.split("'")[1]
        return ("timer", int(seconds))
    elif "<alarm:" in content:
        alarm_time = content.split("'")[1]
        return ("alarm", alarm_time)
    return None



def check_timer_end(question):
    print(f"Checking if user wants to end timer. Question: '{question}'")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "If the user wants to end the timer, return 'End timer'. Otherwise, return 'Continue timer'."},
            {"role": "user", "content": question}
        ]
    )
    result = response.choices[0].message.content.strip().lower()
    print(f"LLM response for timer end check: '{result}'")
    return result




def generate_search_query(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": """Generate a concise and effective search query based on the user's question. Follow these guidelines:

1. Focus on key terms and concepts from the question.
2. Remove unnecessary words like articles, pronouns, and filler phrases.
3. Use quotation marks for exact phrases if needed.
4. Include synonyms or related terms if they might yield better results.
5. Limit the query to 5-7 words maximum for optimal search performance.
6. If the question is about a current event, include the current year.
7. For questions about comparisons, include both items being compared.
8. For questions about definitions or explanations, start with "define" or "explain" as appropriate.

Your task is to create a search query that will yield the most relevant and accurate results for the user's question."""},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content.strip()
