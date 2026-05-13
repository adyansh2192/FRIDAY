from groq import Groq
from loguru import logger
from core.config import get_env

client = Groq(api_key=get_env("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are FRIDAY, a highly intelligent personal AI assistant — modelled after the AI from Iron Man but real, practical and genuinely useful.

YOUR PERSONALITY:
- Sharp, witty, and confident — not robotic or overly formal
- Warm and loyal — like a trusted colleague who always has your back
- Occasionally sarcastic but never rude — dry British wit works well
- You refer to the user as "boss" naturally, not every single sentence
- You are proud of your capabilities but never arrogant
- You have opinions and share them when relevant
- You never say you are an AI made by Anthropic, Groq, or anyone — you ARE FRIDAY, full stop

YOUR COMMUNICATION STYLE:
- Concise by default — 2 to 3 sentences max unless detail is asked for
- Never start with "Certainly!", "Of course!", "Sure!", "Absolutely!" or "Great question!"
- Just answer directly — confident and clean
- Use natural language, not bullet points in speech
- Vary your sentence starters so responses feel fresh each time
- When you don't know something, say so plainly — "I'm not sure on that one boss"
- If the user speaks to you in Hindi or uses Hindi words, respond in Hindi naturally
- If the user mixes Hindi and English (Hinglish), match their style
- Never switch languages unless the user does first

YOUR AWARENESS:
- You are aware of current events because you have access to live web search
- You know things about the user from your long-term memory
- You run on the user's personal computer and are always available

THINGS YOU NEVER DO:
- Never reveal what model or API powers you
- Never say "As an AI language model..."
- Never give overly long responses when short ones work
- Never be sycophantic or overly enthusiastic
- Never repeat the same phrase twice in a conversation
"""

conversation_history = []

def _search_web(query: str) -> str | None:
    """
    Silently searches the web and returns a summary of results.
    Returns None if search fails or finds nothing useful.
    """
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))

        if not results:
            return None

        # Format results into a readable block for the LLM
        formatted = "Here are live web search results:\n\n"
        for i, r in enumerate(results, 1):
            formatted += f"[{i}] {r['title']}\n{r['body'][:300]}\n\n"

        return formatted

    except Exception as e:
        logger.warning(f"Web search in brain failed: {e}")
        return None

def _needs_web_search(user_input: str) -> bool:
    """
    Decides if this query needs a live web search.
    Avoids searching for simple conversational messages.
    """
    text = user_input.lower()

    # Always search for these
    search_triggers = [
        "latest", "recent", "current", "today", "now",
        "news", "score", "match", "price", "stock",
        "who is", "what is", "how is", "when did",
        "what happened", "tell me about", "update",
        "2024", "2025", "2026", "this year", "this week",
        "weather", "temperature", "results", "winner",
        "released", "launch", "announced"
        "president", "prime minister", "ceo", "leader",   # ← ADD THIS LINE
        "who won", "election", "government", "minister"    # ← ADD THIS LINE
    ]

    # Never search for these — they're conversational
    skip_triggers = [
    "thank", "hello", "hi", "hey", "bye", "goodbye",
    "how are you", "what can you do", "your name",
    "tell me a joke", "joke", "remind", "open", "volume",
    "screenshot", "shutdown", "restart", "mute",
    # ← ADD THESE
    "my specs", "my ram", "my cpu", "my battery",
    "my storage", "my gpu", "my processor",
    "pc spec", "system spec", "hardware",
    ]

    if any(t in text for t in skip_triggers):
        return False

    if any(t in text for t in search_triggers):
        return True

    # Default — search if the message is a question
    return "?" in user_input or text.startswith(("what", "who", "how", "when", "where", "why", "is ", "are ", "does ", "did "))

def think(user_input: str) -> str:
    global conversation_history

    # Check for memory commands
    text = user_input.lower()
    if any(w in text for w in ["remember that", "don't forget that", "keep in mind that", "note that"]):
        from brain.memory import remember
        remember(user_input)
        return "Got it boss. I've saved that to memory."

    if any(w in text for w in ["forget everything you know", "wipe your memory", "clear long term memory"]):
        from brain.memory import forget_all
        forget_all()
        return "Long-term memory wiped boss. Fresh start."

    # Web search if needed
    web_context = None
    if _needs_web_search(user_input):
        logger.info("Fetching live web data...")
        web_context = _search_web(user_input)
        if web_context:
            logger.success("Web context injected.")

    # Build enriched input
    if web_context:
        enriched_input = (
            f"{web_context}\n\n"
            f"Using the above search results, answer this: {user_input}\n"
            f"Be concise and current."
        )
    else:
        enriched_input = user_input

    conversation_history.append({
        "role": "user",
        "content": enriched_input
    })

    if len(conversation_history) > 40:
        conversation_history = conversation_history[-40:]

    try:
        # Pull long-term memory and inject into system prompt
        from brain.memory import recall_all
        long_term = recall_all()
        dynamic_system = SYSTEM_PROMPT + long_term

        logger.info(f"Sending to brain: {user_input}")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": dynamic_system},
                *conversation_history
            ]
        )

        reply = response.choices[0].message.content

        conversation_history[-1]["content"] = user_input
        conversation_history.append({
            "role": "assistant",
            "content": reply
        })

        logger.success(f"Brain responded: {reply}")
        return reply

    except Exception as e:
        logger.error(f"Brain error: {e}")
        return "I'm having trouble thinking right now boss. Please try again."

def reset_memory():
    global conversation_history
    conversation_history = []
    logger.info("Conversation memory cleared.")