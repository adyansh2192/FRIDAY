import requests
from core.config import get_env

api_key = get_env("OPENWEATHER_API_KEY")
city = "Delhi"

print(f"API Key found: {api_key[:8]}..." if api_key else "NO API KEY FOUND")

url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
response = requests.get(url)
data = response.json()

print(f"Status code: {response.status_code}")
print(f"Response: {data}")