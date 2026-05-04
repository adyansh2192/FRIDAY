import re
from simpleeval import simple_eval, EvalWithCompoundTypes
from skills.base import BaseSkill
from loguru import logger

class CalculatorSkill(BaseSkill):

    TRIGGERS = [
        "calculate", "compute", "solve", "math",
        "what is", "what's", "how much is",
        "plus", "minus", "times", "divided by",
        "multiply", "divide", "add", "subtract",
        "percent", "percentage", "square root",
        "power", "squared", "cubed"
    ]

    # Only trigger if there's also a number in the input
    def can_handle(self, user_input: str) -> bool:
        text = user_input.lower()
        has_trigger = any(t in text for t in self.TRIGGERS)
        has_number  = bool(re.search(r'\d', text))
        return has_trigger and has_number

    def execute(self, user_input: str) -> str:
        text = user_input.lower().strip()

        try:
            # Handle percentage queries first
            # "what is 15 percent of 8500"
            pct_match = re.search(
                r'(\d+\.?\d*)\s*(?:percent|%)\s*of\s*(\d+\.?\d*)', text
            )
            if pct_match:
                pct    = float(pct_match.group(1))
                total  = float(pct_match.group(2))
                result = (pct / 100) * total
                return f"{pct}% of {total} is {self._format(result)}, boss."

            # Handle square root
            # "square root of 144"
            sqrt_match = re.search(r'square root of (\d+\.?\d*)', text)
            if sqrt_match:
                num    = float(sqrt_match.group(1))
                result = num ** 0.5
                return f"The square root of {self._format(num)} is {self._format(result)}, boss."

            # Handle "X squared" or "X cubed"
            power_match = re.search(r'(\d+\.?\d*)\s*(squared|cubed)', text)
            if power_match:
                num    = float(power_match.group(1))
                word   = power_match.group(2)
                exp    = 2 if word == "squared" else 3
                result = num ** exp
                return f"{self._format(num)} {word} is {self._format(result)}, boss."

            # Convert spoken words to math symbols
            expression = self._words_to_symbols(text)

            # Strip non-math characters
            expression = self._clean_expression(expression)

            if not expression:
                return "I couldn't parse that math expression boss. Try saying it differently."

            # Safely evaluate the expression
            result = simple_eval(expression)
            return f"The answer is {self._format(result)}, boss."

        except ZeroDivisionError:
            return "Can't divide by zero boss. Even I have limits."
        except Exception as e:
            logger.warning(f"Calculator failed: {e}")
            return "I couldn't solve that one boss. Try rephrasing it."

    def _words_to_symbols(self, text: str) -> str:
        """Convert spoken math words into symbols."""
        replacements = {
            # Operations
            " plus "        : " + ",
            " add "         : " + ",
            " added to "    : " + ",
            " minus "       : " - ",
            " subtract "    : " - ",
            " times "       : " * ",
            " multiplied by": " * ",
            " multiply by " : " * ",
            " x "           : " * ",
            " divided by "  : " / ",
            " divide by "   : " / ",
            " over "        : " / ",
            " to the power of ": " ** ",
            " power "       : " ** ",
            " mod "         : " % ",

            # Filler words to remove
            "what is "      : "",
            "what's "       : "",
            "calculate "    : "",
            "compute "      : "",
            "solve "        : "",
            "how much is "  : "",
            "the answer to ": "",
            "math "         : "",
        }

        for word, symbol in replacements.items():
            text = text.replace(word, symbol)

        return text

    def _clean_expression(self, text: str) -> str:
        """Strip anything that isn't a valid math character."""
        # Keep only numbers, operators, dots, parentheses, spaces
        cleaned = re.sub(r'[^0-9+\-*/().\s\*\*]', '', text)
        return cleaned.strip()

    def _format(self, value: float) -> str:
        """Format the result — remove .0 for whole numbers."""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(round(value, 6))