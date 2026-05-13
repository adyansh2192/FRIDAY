from loguru import logger
from skills.alarm_skill import AlarmSkill
from skills.briefing_skill import BriefingSkill
from skills.calculator_skill import CalculatorSkill
from skills.datetime_skill import DateTimeSkill
from skills.launcher_skill import LauncherSkill
from skills.music_skill import MusicSkill
from skills.news_skill import NewsSkill
from skills.reminder_skill import ReminderSkill
from skills.search_skill import SearchSkill
from skills.system_skill import SystemSkill
from skills.system_stats_skill import SystemStatsSkill
from skills.weather_skill import WeatherSkill
from skills.website_skill import WebsiteSkill

SKILLS = [
    BriefingSkill(),
    AlarmSkill(),       # ← must be before DateTimeSkill
    DateTimeSkill(),
    CalculatorSkill(),
    WeatherSkill(),
    NewsSkill(),
    SystemStatsSkill(),
    LauncherSkill(),
    WebsiteSkill(),
    ReminderSkill(),
    SystemSkill(),
    MusicSkill(),
    SearchSkill(),      # always last
]

def route(user_input: str) -> str | None:
    for skill in SKILLS:
        if skill.can_handle(user_input):
            logger.info(f"Routed to: {skill.__class__.__name__}")
            return skill.execute(user_input)
    logger.info("No skill matched — falling back to brain.")
    return None