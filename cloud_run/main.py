import logging
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
import httpx
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP with disabled DNS rebinding protection for Cloud Run
mcp = FastMCP(
    "Weather Server",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

@mcp.tool()
async def get_weather(location: str) -> str:
    """
    Fetch weather for a given location.
    
    Args:
        location (str): The name of the city/location (e.g., "Paris", "New York").
    """
    if not location:
        return "Error: Location parameter is required."

    logger.info(f"Fetching weather for location: {location}")

    async with httpx.AsyncClient() as client:
        # 1. Geocoding: Get Lat/Lon
        try:
            geo_response = await client.get(
                GEOCODING_URL,
                params={"name": location, "count": 1, "language": "en", "format": "json"}
            )
            geo_response.raise_for_status()
            geo_data = geo_response.json()
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return f"Error resolving location: {str(e)}"

        if not geo_data.get("results"):
            return f"Error: Location '{location}' not found."

        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        resolved_name = result.get("name", location)
        country = result.get("country", "")

        # 2. Weather: Get Current Weather
        try:
            weather_response = await client.get(
                WEATHER_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": True,
                    "temperature_unit": "celsius"
                }
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return f"Error fetching weather data: {str(e)}"

        current = weather_data.get("current_weather")
        if not current:
            return "Error: Weather data unavailable."

        return (
            f"The current temperature in {resolved_name}, {country} is "
            f"{current['temperature']}°C with a windspeed of {current['windspeed']} km/h."
        )

# Get the Starlette app for Streamable HTTP
app = mcp.streamable_http_app()

if __name__ == "__main__":
    # Run the app using uvicorn
    # Port 8080 is standard for Cloud Run
    logger.info("Starting MCP Weather Server on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
