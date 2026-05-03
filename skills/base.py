class BaseSkill:
    """
    Every skill inherits from this.
    Keeps all skills consistent and pluggable.
    """

    def can_handle(self, user_input: str) -> bool:
        """
        Return True if this skill should handle the input.
        Each skill decides this based on keywords.
        """
        raise NotImplementedError

    def execute(self, user_input: str) -> str:
        """
        Run the skill and return a response string.
        FRIDAY will speak this response.
        """
        raise NotImplementedError