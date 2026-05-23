"""whereismyip - IP geolocation using free, no-registration services.

Queries multiple geolocation providers and returns the first successful response.
See README at https://github.com/asweigart/whereismyip for usage.
"""
import ipaddress
import json
import random
import threading
import time
import urllib.parse
import urllib.request
from typing import Optional

try:
    import importlib.metadata as _metadata
except ImportError:
    _metadata = None  # type: ignore

try:
    __version__ = _metadata.version("whereismyip") if _metadata else "0.0.0+unknown"
except Exception:
    __version__ = "0.0.0+unknown"

try:
    import whatismyip
    _HAS_WHATISMYIP = True
except ImportError:
    _HAS_WHATISMYIP = False

# ISO 3166-1 alpha-2 country code to English country name mapping.
# Source: https://github.com/stefangabos/world_countries (public domain).
COUNTRY_NAMES = {
    "AD": "Andorra",
    "AE": "United Arab Emirates",
    "AF": "Afghanistan",
    "AG": "Antigua and Barbuda",
    "AL": "Albania",
    "AM": "Armenia",
    "AO": "Angola",
    "AR": "Argentina",
    "AT": "Austria",
    "AU": "Australia",
    "AZ": "Azerbaijan",
    "BA": "Bosnia and Herzegovina",
    "BB": "Barbados",
    "BD": "Bangladesh",
    "BE": "Belgium",
    "BF": "Burkina Faso",
    "BG": "Bulgaria",
    "BH": "Bahrain",
    "BI": "Burundi",
    "BJ": "Benin",
    "BN": "Brunei Darussalam",
    "BO": "Bolivia, Plurinational State of",
    "BR": "Brazil",
    "BS": "Bahamas",
    "BT": "Bhutan",
    "BW": "Botswana",
    "BY": "Belarus",
    "BZ": "Belize",
    "CA": "Canada",
    "CD": "Congo, Democratic Republic of the",
    "CF": "Central African Republic",
    "CG": "Congo",
    "CH": "Switzerland",
    "CI": "Côte d'Ivoire",
    "CL": "Chile",
    "CM": "Cameroon",
    "CN": "China",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "CU": "Cuba",
    "CV": "Cabo Verde",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DE": "Germany",
    "DJ": "Djibouti",
    "DK": "Denmark",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EE": "Estonia",
    "EG": "Egypt",
    "ER": "Eritrea",
    "ES": "Spain",
    "ET": "Ethiopia",
    "FI": "Finland",
    "FJ": "Fiji",
    "FM": "Micronesia, Federated States of",
    "FR": "France",
    "GA": "Gabon",
    "GB": "United Kingdom of Great Britain and Northern Ireland",
    "GD": "Grenada",
    "GE": "Georgia",
    "GH": "Ghana",
    "GM": "Gambia",
    "GN": "Guinea",
    "GQ": "Equatorial Guinea",
    "GR": "Greece",
    "GT": "Guatemala",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HN": "Honduras",
    "HR": "Croatia",
    "HT": "Haiti",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IN": "India",
    "IQ": "Iraq",
    "IR": "Iran, Islamic Republic of",
    "IS": "Iceland",
    "IT": "Italy",
    "JM": "Jamaica",
    "JO": "Jordan",
    "JP": "Japan",
    "KE": "Kenya",
    "KG": "Kyrgyzstan",
    "KH": "Cambodia",
    "KI": "Kiribati",
    "KM": "Comoros",
    "KN": "Saint Kitts and Nevis",
    "KP": "Korea, Democratic People's Republic of",
    "KR": "Korea, Republic of",
    "KW": "Kuwait",
    "KZ": "Kazakhstan",
    "LA": "Lao People's Democratic Republic",
    "LB": "Lebanon",
    "LC": "Saint Lucia",
    "LI": "Liechtenstein",
    "LK": "Sri Lanka",
    "LR": "Liberia",
    "LS": "Lesotho",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "LY": "Libya",
    "MA": "Morocco",
    "MC": "Monaco",
    "MD": "Moldova, Republic of",
    "ME": "Montenegro",
    "MG": "Madagascar",
    "MH": "Marshall Islands",
    "MK": "North Macedonia",
    "ML": "Mali",
    "MM": "Myanmar",
    "MN": "Mongolia",
    "MR": "Mauritania",
    "MT": "Malta",
    "MU": "Mauritius",
    "MV": "Maldives",
    "MW": "Malawi",
    "MX": "Mexico",
    "MY": "Malaysia",
    "MZ": "Mozambique",
    "NA": "Namibia",
    "NE": "Niger",
    "NG": "Nigeria",
    "NI": "Nicaragua",
    "NL": "Netherlands",
    "NO": "Norway",
    "NP": "Nepal",
    "NR": "Nauru",
    "NZ": "New Zealand",
    "OM": "Oman",
    "PA": "Panama",
    "PE": "Peru",
    "PG": "Papua New Guinea",
    "PH": "Philippines",
    "PK": "Pakistan",
    "PL": "Poland",
    "PT": "Portugal",
    "PW": "Palau",
    "PY": "Paraguay",
    "QA": "Qatar",
    "RO": "Romania",
    "RS": "Serbia",
    "RU": "Russian Federation",
    "RW": "Rwanda",
    "SA": "Saudi Arabia",
    "SB": "Solomon Islands",
    "SC": "Seychelles",
    "SD": "Sudan",
    "SE": "Sweden",
    "SG": "Singapore",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "SL": "Sierra Leone",
    "SM": "San Marino",
    "SN": "Senegal",
    "SO": "Somalia",
    "SR": "Suriname",
    "SS": "South Sudan",
    "ST": "Sao Tome and Principe",
    "SV": "El Salvador",
    "SY": "Syrian Arab Republic",
    "SZ": "Eswatini",
    "TD": "Chad",
    "TG": "Togo",
    "TH": "Thailand",
    "TJ": "Tajikistan",
    "TL": "Timor-Leste",
    "TM": "Turkmenistan",
    "TN": "Tunisia",
    "TO": "Tonga",
    "TR": "Türkiye",
    "TT": "Trinidad and Tobago",
    "TV": "Tuvalu",
    "TZ": "Tanzania, United Republic of",
    "UA": "Ukraine",
    "UG": "Uganda",
    "US": "United States of America",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VC": "Saint Vincent and the Grenadines",
    "VE": "Venezuela, Bolivarian Republic of",
    "VN": "Viet Nam",
    "VU": "Vanuatu",
    "WS": "Samoa",
    "YE": "Yemen",
    "ZA": "South Africa",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
}

# Override the ISO long-form names with the common short forms that the
# major geolocation providers (ipwhois.io, ipapi.co, etc.) actually return,
# so the `country` field is consistent regardless of which provider answers.
_SHORT_NAME_OVERRIDES = {
    "BO": "Bolivia",
    "CD": "Democratic Republic of the Congo",
    "FM": "Micronesia",
    "GB": "United Kingdom",
    "IR": "Iran",
    "KR": "South Korea",
    "LA": "Laos",
    "MD": "Moldova",
    "RU": "Russia",
    "SY": "Syria",
    "TZ": "Tanzania",
    "US": "United States",
    "VE": "Venezuela",
    "VN": "Vietnam",
}
COUNTRY_NAMES.update(_SHORT_NAME_OVERRIDES)

__all__ = [
    "CouldNotGeolocate",
    "WhatIsMyIPPackageNotInstalled",
    "clear_cache",
    "geolocate_ipwhois_io",
    "geolocate_ipapi_co",
    "geolocate_ipinfo_lite",
    "geolocate_findip_net",
    "whereismyip",
    "whereismyip_dict",
]

_DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_DEFAULT_CACHE_TTL = 2.0

_rng = random.Random()

_cache_lock = threading.Lock()
_cache: dict = {}  # key -> (expires_at_monotonic, value_dict)


def _cache_get(key):
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            _cache.pop(key, None)
            return None
        return value


def _cache_put(key, value, ttl):
    with _cache_lock:
        _cache[key] = (time.monotonic() + ttl, value)


def clear_cache() -> None:
    """Drop all cached geolocation results."""
    with _cache_lock:
        _cache.clear()


class CouldNotGeolocate(Exception):
    """Raised when no geolocation provider could resolve the IP address."""


class WhatIsMyIPPackageNotInstalled(Exception):
    """Raised when auto-detection of your public IP is requested but the
    optional `whatismyip` package is not installed."""


def _validate_and_quote_ip(ip_address: str) -> str:
    """Validate ip_address is a real IPv4/IPv6 address and return it URL-quoted."""
    ipaddress.ip_address(ip_address)
    return urllib.parse.quote(ip_address, safe="")


def _get_my_ip_if_needed(ip_address: str = "") -> str:
    if ip_address == "":
        if not _HAS_WHATISMYIP:
            raise WhatIsMyIPPackageNotInstalled(
                "The 'whatismyip' package is required to auto-detect your "
                "public IP. Install it or pass ip_address."
            )
        ip_address = whatismyip.whatismyip()
    return ip_address


def _http_get_json(url: str, timeout: float, user_agent: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def geolocate_ipwhois_io(
    ip_address: str = "",
    timeout: float = 2.0,
    user_agent: str = _DEFAULT_USER_AGENT,
) -> dict:
    """
    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param float timeout: Socket timeout in seconds
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    safe_ip = _validate_and_quote_ip(ip_address)
    url = f"https://ipwhois.app/json/{safe_ip}"
    data = _http_get_json(url, timeout, user_agent)
    if not data.get("ip"):
        raise CouldNotGeolocate(f"ipwhois.io returned no usable data: {data!r}")
    return data


def geolocate_ipapi_co(
    ip_address: str = "",
    timeout: float = 2.0,
    user_agent: str = _DEFAULT_USER_AGENT,
) -> dict:
    """
    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param float timeout: Socket timeout in seconds
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    safe_ip = _validate_and_quote_ip(ip_address)
    url = f"https://ipapi.co/{safe_ip}/json/"
    data = _http_get_json(url, timeout, user_agent)
    if data.get("error") or not data.get("ip"):
        raise CouldNotGeolocate(f"ipapi.co returned no usable data: {data!r}")
    return data


def geolocate_ipinfo_lite(
    ip_address: str = "",
    timeout: float = 2.0,
    user_agent: str = _DEFAULT_USER_AGENT,
) -> dict:
    """
    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param float timeout: Socket timeout in seconds
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    safe_ip = _validate_and_quote_ip(ip_address)
    url = f"https://ipinfo.io/{safe_ip}/json"
    data = _http_get_json(url, timeout, user_agent)
    if not data.get("ip"):
        raise CouldNotGeolocate(f"ipinfo.io returned no usable data: {data!r}")
    return data


def geolocate_findip_net(
    ip_address: str = "",
    timeout: float = 2.0,
    user_agent: str = _DEFAULT_USER_AGENT,
) -> dict:
    """
    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param float timeout: Socket timeout in seconds
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    safe_ip = _validate_and_quote_ip(ip_address)
    url = f"https://findip.net/{safe_ip}.json"
    data = _http_get_json(url, timeout, user_agent)
    traits = data.get("traits") or {}
    if not traits.get("ip_address"):
        raise CouldNotGeolocate(f"findip.net returned no usable data: {data!r}")
    return data


_GEO_FUNCS = (
    geolocate_ipwhois_io,
    geolocate_ipapi_co,
    geolocate_ipinfo_lite,
    geolocate_findip_net,
)

_COMMON_KEYS = (
    "ip",
    "city",
    "region",
    "country",
    "country_code",
    "latitude",
    "longitude",
)


def _normalize_ipwhois_io(data: dict) -> dict:
    return {
        "ip": data.get("ip"),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country"),
        "country_code": data.get("country_code"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
    }


def _normalize_ipapi_co(data: dict) -> dict:
    code = data.get("country") or data.get("country_code")
    return {
        "ip": data.get("ip"),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": data.get("country_name") or (COUNTRY_NAMES.get(code) if code else None),
        "country_code": code,
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
    }


def _normalize_ipinfo_lite(data: dict) -> dict:
    loc = data.get("loc", "")
    lat: Optional[float] = None
    lng: Optional[float] = None
    if isinstance(loc, str) and "," in loc:
        lat_str, _, lng_str = loc.partition(",")
        try:
            lat = float(lat_str)
            lng = float(lng_str)
        except ValueError:
            lat = lng = None
    code = data.get("country")
    return {
        "ip": data.get("ip"),
        "city": data.get("city"),
        "region": data.get("region"),
        "country": COUNTRY_NAMES.get(code, code) if code else None,
        "country_code": code,
        "latitude": lat,
        "longitude": lng,
    }


def _normalize_findip_net(data: dict) -> dict:
    country = data.get("country") or {}
    city = data.get("city") or {}
    location = data.get("location") or {}
    traits = data.get("traits") or {}
    subdivisions = data.get("subdivisions") or []
    region = None
    if subdivisions and isinstance(subdivisions[0], dict):
        names = subdivisions[0].get("names") or {}
        region = names.get("en")
    city_names = city.get("names") or {}
    country_names = country.get("names") or {}
    return {
        "ip": traits.get("ip_address"),
        "city": city_names.get("en"),
        "region": region,
        "country": country_names.get("en"),
        "country_code": country.get("iso_code"),
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
    }


_NORMALIZERS = {
    geolocate_ipwhois_io: _normalize_ipwhois_io,
    geolocate_ipapi_co: _normalize_ipapi_co,
    geolocate_ipinfo_lite: _normalize_ipinfo_lite,
    geolocate_findip_net: _normalize_findip_net,
}


def _try_providers(
    ip_address: str = "",
    timeout: float = 2.0,
    user_agent: str = _DEFAULT_USER_AGENT,
    providers=_GEO_FUNCS,
):
    funcs = list(providers)
    _rng.shuffle(funcs)
    errors = []
    for func in funcs:
        try:
            result = func(ip_address, timeout=timeout, user_agent=user_agent)
            if result:
                return func, result
        except Exception as exc:
            errors.append((func.__name__, exc))
    if errors:
        details = "; ".join(f"{name}: {exc}" for name, exc in errors)
        raise CouldNotGeolocate(f"All providers failed: {details}")
    raise CouldNotGeolocate("All geolocation providers returned empty results")


def whereismyip_dict(
    ip_address: str = "",
    timeout: float = 2.0,
    attempts: int = 2,
    user_agent: str = _DEFAULT_USER_AGENT,
    providers=_GEO_FUNCS,
    cache_ttl: float = _DEFAULT_CACHE_TTL,
) -> dict:
    """
    Returns a normalized dict of geolocation fields from the first successful provider.

    Keys: ip, city, region, country (full name), country_code (ISO alpha-2),
    latitude, longitude. Values may be None when the chosen provider does not
    expose that field.

    Successful results are cached in-process for `cache_ttl` seconds (default
    2.0). Pass cache_ttl=0 to bypass the cache. Use clear_cache() to drop it.

    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param float timeout: Socket timeout in seconds
    :param int attempts: Number of full passes through all providers. Total
        network calls can be up to attempts * len(providers). The auto-IP
        lookup via `whatismyip` is not retried by this loop.
    :param str user_agent: Value to use for the User-Agent HTTP header
    :param float cache_ttl: TTL in seconds for the in-process result cache.
        Set to 0 to disable caching for this call.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    cache_key = None
    if cache_ttl > 0:
        cache_key = (ip_address, tuple(providers))
        cached = _cache_get(cache_key)
        if cached is not None:
            return dict(cached)

    ip_address = _get_my_ip_if_needed(ip_address)
    last_exception: Optional[Exception] = None
    for _ in range(attempts):
        try:
            func, data = _try_providers(
                ip_address, timeout=timeout, user_agent=user_agent, providers=providers
            )
            normalizer = _NORMALIZERS.get(func)
            result = normalizer(data) if normalizer else {k: data.get(k) for k in _COMMON_KEYS}
            if cache_key is not None:
                _cache_put(cache_key, result, cache_ttl)
            return dict(result)
        except Exception as exc:
            last_exception = exc
    raise last_exception  # type: ignore[misc]


def whereismyip(
    ip_address: str = "",
    timeout: float = 2.0,
    attempts: int = 2,
    user_agent: str = _DEFAULT_USER_AGENT,
    providers=_GEO_FUNCS,
    cache_ttl: float = _DEFAULT_CACHE_TTL,
) -> str:
    """
    Returns '<city>, <region>, <country>'.

    Successful results are cached in-process for `cache_ttl` seconds (default
    2.0). Pass cache_ttl=0 to bypass the cache. Use clear_cache() to drop it.

    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param float timeout: Socket timeout in seconds
    :param int attempts: Number of full passes through all providers. Total
        network calls can be up to attempts * len(providers). The auto-IP
        lookup via `whatismyip` is not retried by this loop.
    :param str user_agent: Value to use for the User-Agent HTTP header
    :param float cache_ttl: TTL in seconds for the in-process result cache.
        Set to 0 to disable caching for this call.
    """
    data = whereismyip_dict(
        ip_address,
        timeout=timeout,
        attempts=attempts,
        user_agent=user_agent,
        providers=providers,
        cache_ttl=cache_ttl,
    )
    city = data.get("city") or ""
    region = data.get("region") or ""
    country = data.get("country") or ""
    return ", ".join(filter(None, (city, region, country)))
