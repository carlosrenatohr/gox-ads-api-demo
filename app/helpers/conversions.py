from google.ads.googleads.client import GoogleAdsClient
from typing import Dict, Optional, List, Any

# Run a GAQL query and return the results as a stream
def run_gaql_stream(client: GoogleAdsClient, customer_id: str, query: str):
    ga = client.get_service("GoogleAdsService")
    return ga.search_stream(customer_id=customer_id, query=query)

# Convert micros to amount
def micros_to_amount(micros: int | float) -> float:
    return round((micros or 0) / 1_000_000.0, 2)

# Safe division
def safe_div(n: float, d: float) -> float:
    return round(n / d, 4) if d else 0.0

def extract_value(obj: Any) -> Any:
    """
    Convert proto-plus values to Python types:
    - Enums -> name (string)
    - Messages with 'name' -> use 'name' if exists (case enums)
    - Numbers/strings -> as is
    """
    if obj is None:
        return None
    # enums proto-plus usually have .name
    name = getattr(obj, "name", None)
    if isinstance(name, str):
        return name
    # messages with .resource_name
    rname = getattr(obj, "resource_name", None)
    if isinstance(rname, str):
        return rname
    # scalar values
    if isinstance(obj, (int, float, str, bool)):
        return obj
    # some proto-plus fields are printed well as str
    try:
        return str(obj)
    except Exception:
        return None

# Pick fields from the row object
def pick_fields(row: Any, fields: List[str]) -> Dict[str, Any]:
    """
    Extract 'campaign.id', 'metrics.clicks', etc. from the row object.
    """
    out: Dict[str, Any] = {}
    for path in fields:
        cur = row
        try:
            for part in path.split("."):
                cur = getattr(cur, part)
            out[path] = extract_value(cur)
        except AttributeError:
            out[path] = None
    return out

# Normalize fields from the user input
def normalize_fields(user_fields: Optional[str], default_fields: List[str]) -> List[str]:
    if user_fields:
        return [f.strip() for f in user_fields.split(",") if f.strip()]
    return default_fields