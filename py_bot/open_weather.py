import aiohttp


BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'


async def fetch_weather(API_KEY, city):
    """Get weather from OpenWeatherMap

    Args:
        API_KEY (str): TOKEN for openweatherapi
        city (str): city name

    Returns:
        str: current weather description
    """
    async with aiohttp.ClientSession() as session:
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric'
        }
        async with session.get(BASE_URL, params=params) as response:
            if response.status == 200:
                weather_data = await response.json()
                return f"""Погода в городе {city}:
                Температура: {weather_data['main']['temp']}°C
                Состояние: {weather_data['weather'][0]['description']}
                Влажность: {weather_data['main']['humidity']}%"""
            else:
                print(f'Error: {response.status}')
                return None
