from google.ads.googleads.client import GoogleAdsClient

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

