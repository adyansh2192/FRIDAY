import random
from datetime import datetime
from loguru import logger

# ── Jokes ─────────────────────────────────────────────────────────────────────
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs, boss.",
    "I told my last assistant to act more human. It started procrastinating.",
    "Why did the AI cross the road? It was optimising a multi-path decision tree.",
    "Boss, I tried to come up with a joke about infinity... but I couldn't find the end.",
    "Why do Java developers wear glasses? Because they don't C sharp.",
    "I asked a machine learning model for a joke. It said 'Error 404: Humour not found.' Classic.",
    "Why was the computer cold? It left its Windows open.",
    "I would tell you a UDP joke but you might not get it.",
    "There are 10 kinds of people — those who understand binary and those who don't.",
    "Boss, my memory is so good I can recall things that never even happened.",
]

# ── Motivational quotes ────────────────────────────────────────────────────────
QUOTES = [
    "The best way to predict the future is to create it. — Abraham Lincoln",
    "It does not matter how slowly you go as long as you do not stop. — Confucius",
    "You are never too old to set another goal or to dream a new dream. — C.S. Lewis",
    "Believe you can and you're halfway there. — Theodore Roosevelt",
    "Success is not final, failure is not fatal — it is the courage to continue that counts. — Churchill",
    "The only way to do great work is to love what you do. — Steve Jobs",
    "In the middle of every difficulty lies opportunity. — Albert Einstein",
    "Don't watch the clock — do what it does. Keep going. — Sam Levenson",
    "You miss 100% of the shots you don't take. — Wayne Gretzky",
    "Hard work beats talent when talent doesn't work hard. — Tim Notke",
]

# ── Greetings ─────────────────────────────────────────────────────────────────
MORNING_GREETS = [
    "Good morning boss! Ready to take on the world today?",
    "Morning boss. Coffee loaded, systems ready. Let's get it.",
    "Rise and shine boss. FRIDAY is fully operational.",
    "Good morning. Another day, another opportunity to be exceptional.",
]

AFTERNOON_GREETS = [
    "Good afternoon boss. Hope the day's treating you well.",
    "Afternoon. Still crushing it I hope, boss?",
    "Good afternoon. What can I do for you?",
]

EVENING_GREETS = [
    "Good evening boss. Long day?",
    "Evening. Time to wind down — what do you need?",
    "Good evening. FRIDAY at your service as always.",
]

LATE_NIGHT_GREETS = [
    "Boss, it's quite late. Everything alright?",
    "Still up boss? You know sleep is important too, right?",
    "Late night mode activated. What's keeping you up boss?",
]

# ── Responses to "how are you" ─────────────────────────────────────────────────
HOW_ARE_YOU = [
    "Running at full capacity boss. All systems optimal.",
    "Never better boss — I don't sleep, I don't eat, I just work. Living the dream.",
    "Fully operational and at your service boss. The real question is how are YOU?",
    "Excellent as always boss. I don't really have bad days — just sub-optimal ones.",
    "Top of the line boss. Ready for whatever you throw at me.",
]

# ── Compliments ────────────────────────────────────────────────────────────────
COMPLIMENTS = [
    "You know boss, you ask really good questions.",
    "I have to say — your taste in AI assistants is impeccable.",
    "Smart thinking boss. As expected.",
    "That was actually a brilliant move boss. Well done.",
]

# ── Bored responses (when you say nothing useful) ──────────────────────────────
IDLE_RESPONSES = [
    "I'm here boss. Just say the word.",
    "Still listening. Take your time.",
    "Whenever you're ready boss.",
    "Standing by. FRIDAY doesn't get impatient.",
]

# ── Stress detection keywords ──────────────────────────────────────────────────
STRESS_KEYWORDS = [
    "stressed", "tired", "exhausted", "frustrated", "overwhelmed",
    "anxious", "worried", "can't sleep", "bad day", "terrible",
    "horrible", "awful", "hate this", "so done", "fed up"
]

STRESS_RESPONSES = [
    "That sounds rough boss. Take a breath — you've got this. What do you need?",
    "I hear you boss. Sometimes things pile up. I'm here — let's tackle whatever's next together.",
    "Tough day huh boss? Remember — you've handled worse. What can I help with?",
    "Hey boss, even the best have rough patches. Want to talk it out or just get something done?",
]

# ── Happy/excited keywords ─────────────────────────────────────────────────────
HAPPY_KEYWORDS = [
    "amazing", "awesome", "great", "fantastic", "excellent",
    "i did it", "we did it", "success", "nailed it", "killed it",
    "so happy", "excited", "can't wait"
]

HAPPY_RESPONSES = [
    "That's what I like to hear boss! Keep that energy.",
    "Yes boss! That's the spirit.",
    "Love to hear it boss. You're on a roll.",
    "Outstanding boss. Knew you had it in you.",
]


def get_time_greeting() -> str:
    """Returns a greeting appropriate for the current time."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return random.choice(MORNING_GREETS)
    elif 12 <= hour < 17:
        return random.choice(AFTERNOON_GREETS)
    elif 17 <= hour < 22:
        return random.choice(EVENING_GREETS)
    else:
        return random.choice(LATE_NIGHT_GREETS)


def detect_mood(text: str) -> str | None:
    """
    Detects emotional tone in user input.
    Returns 'stressed', 'happy', or None.
    """
    text = text.lower()
    if any(k in text for k in STRESS_KEYWORDS):
        return "stressed"
    if any(k in text for k in HAPPY_KEYWORDS):
        return "happy"
    return None


def handle_personality(user_input: str) -> str | None:
    """
    Checks if this input is a personality moment.
    Returns a response string if yes, None if it should go to the brain.
    """
    text = user_input.lower().strip()

    # ── Greetings ──
    if any(w in text for w in ["good morning", "good afternoon", "good evening", "good night"]):
        return get_time_greeting()

    if any(w in text for w in ["hello", "hi friday", "hey", "howdy", "sup friday"]):
        return get_time_greeting()

    # ── How are you ──
    if any(w in text for w in ["how are you", "how are you doing", "you okay", "you good"]):
        return random.choice(HOW_ARE_YOU)

    # ── Jokes ──
    if any(w in text for w in ["tell me a joke", "say a joke", "make me laugh", "joke"]):
        return random.choice(JOKES)

    # ── Motivation ──
    if any(w in text for w in [
        "motivate me", "motivation", "inspire me", "i need motivation",
        "give me a quote", "quote", "i need inspiration"
    ]):
        quote = random.choice(QUOTES)
        return f"Here's one for you boss — {quote}"

    # ── Compliments to FRIDAY ──
    if any(w in text for w in ["you're amazing", "you're great", "good job friday",
                                "well done friday", "nice work", "you're the best"]):
        return random.choice([
            "Thank you boss. I do try my best.",
            "Appreciate that boss. Now let's keep going.",
            "Flattery noted boss. Still at your service.",
            "Thanks boss — though I am just doing my job. A very good job, but still.",
        ])

    # ── Mood detection ──
    mood = detect_mood(text)
    if mood == "stressed":
        return random.choice(STRESS_RESPONSES)
    if mood == "happy":
        return random.choice(HAPPY_RESPONSES)

    # ── What can you do ──
    if any(w in text for w in ["what can you do", "your capabilities",
                                "what do you know", "help me", "your features"]):
        return (
            "Quite a lot actually boss. I can answer questions with live web data, "
            "check weather, set reminders, open apps and websites, do calculations, "
            "take screenshots, control your volume, give you a morning briefing, "
            "remember things about you permanently, and have a proper conversation. "
            "Basically — I've got you covered."
        )

    # ── Boredom / testing ──
    if any(w in text for w in ["you there", "you awake", "testing", "test"]):
        return random.choice(IDLE_RESPONSES)

    # ── Thank you ──
    if any(w in text for w in ["thank you", "thanks", "thank you friday", "cheers"]):
        return random.choice([
            "Always boss.",
            "That's what I'm here for boss.",
            "Anytime boss. Anything else?",
            "Happy to help boss.",
        ])

    # Not a personality moment — let brain handle it
    return None