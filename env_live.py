import os

from data_fetch.envdata import get_env_data, get_coords_from_place

def _load_dotenv_fallback(dotenv_path: str = ".env") -> None:
    try:
        with open(dotenv_path, "r", encoding="utf-8") as file:
            for raw_line in file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ.setdefault(key, value)
    except FileNotFoundError:
        return


try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # If python-dotenv isn't installed, values can still be provided via OS env vars.
    _load_dotenv_fallback()

LOCATIONIQ_KEY = os.getenv("LOCATIONIQ_KEY")
OWM_KEY = os.getenv("OWM_KEY")
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")

place = os.getenv("PLACE", "Chittarikkal, Kerala, India")  # You can change this to any place you want

if not place:
    print("❌ No place entered.")
    exit()

missing = [name for name, value in {
    "LOCATIONIQ_KEY": LOCATIONIQ_KEY,
    "OWM_KEY": OWM_KEY,
    "WEATHERAPI_KEY": WEATHERAPI_KEY,
}.items() if not value]

if missing:
    print("❌ Missing API key(s): " + ", ".join(missing))
    print("   Add them to your .env file or set them as environment variables.")
    exit()

lat, lon = get_coords_from_place(place, LOCATIONIQ_KEY)

if lat is not None and lon is not None:
    env_data = get_env_data(lat, lon, OWM_KEY, WEATHERAPI_KEY)

    print(f"\n📊 Environmental Data for {place}")
    print("=" * 70)

    for key, value in env_data.items():
        print(f"{key}: {value}")
else:
    print("❌ Could not retrieve coordinates.")