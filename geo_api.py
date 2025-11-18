# geo_api.py
import os
import requests

# Read key from env (or Streamlit secrets if you want later)
API_KEY = os.getenv("GEOSUPPORT_API_KEY")

# TODO: replace this with the real base URL from the docs
BASE_URL = "https://a030-goat.nyc.gov/GOAT/Function1A"   # placeholder!

def lookup_zoning_for_address(address: str) -> dict | None:
    """
    Call the NYC Geosupport API for a given address.
    Return parsed JSON, or None if something fails.
    """
    if not API_KEY:
        # You can also raise if you prefer
        return None

    try:
        resp = requests.get(
            BASE_URL,
            params={"address": address},
            headers={"x-api-key": API_KEY},   # or whatever header the docs say
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print("Geosupport error:", e)
        return None
