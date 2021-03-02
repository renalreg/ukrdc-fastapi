from fastapi_auth0 import Auth0

auth = Auth0(
    domain="renalreg.eu.auth0.com", api_audience="https://app.ukrdc.org/api", scopes={}
)
