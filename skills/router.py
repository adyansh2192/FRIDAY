from loguru import logger
from skills.datetime_skill import DateTimeSkill
from skills.search_skill import SearchSkill
from skills.weather_skill import WeatherSkill
from skills.launcher_skill import LauncherSkill
from skills.reminder_skill import ReminderSkill
from skills.system_skill import SystemSkill
from skills.website_skill import WebsiteSkill
from skills.briefing_skill import BriefingSkill

SKILLS = [
    BriefingSkill(),    # first — catches "good morning" before anything else
    DateTimeSkill(),
    WeatherSkill(),
    LauncherSkill(),
    WebsiteSkill(),     # before search so "open youtube" doesn't go to search
    ReminderSkill(),
    SystemSkill(),
    SearchSkill(),      # widest catcher — always last
]

def route(user_input: str) -> str | None:
    for skill in SKILLS:
        if skill.can_handle(user_input):
            logger.info(f"Routed to: {skill.__class__.__name__}")
            return skill.execute(user_input)
    logger.info("No skill matched — falling back to brain.")
    return None