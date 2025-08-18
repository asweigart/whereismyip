import json
import urllib.request
import urllib.error
import random
try:
    import whatismyip
except:
    pass  # whatismyip is not required.

class CouldNotGeolocate(Exception):
    pass

class WhatIsMyIPPackageNotInstalled(Exception):
    pass

"""
Commenting this out because it does not provide https access for free.

def geolocate_ip_api_com(
    ip_address: str = "",
    timeout: int = 2,
    user_agent: str = "python-urllib",
) -> dict:
    if ip_address == '': ip_address = whatismyip.whatismyip()
    url = f"http://ip-api.com/json/{ip_address}"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.load(response)
        if data.get("status") == "success":
            return data
    raise CouldNotGeolocate
"""

def _get_my_ip_if_needed(ip_address: str = "") -> str:
    if ip_address == '':
        try:
            ip_address = whatismyip.whatismyip()
        except NameError:
            raise WhatIsMyIPPackageNotInstalled
    return ip_address


def geolocate_ipwhois_io(
    ip_address: str = "",
    timeout: int = 2,
    user_agent: str = "python-urllib",
) -> dict:
    """
    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param int timeout: Socket timeout in seconds
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    url = f"https://ipwhois.app/json/{ip_address}"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.load(response)
        if data.get("success", True):
            return data
    raise CouldNotGeolocate


def geolocate_ipapi_co(
    ip_address: str = "",
    timeout: int = 2,
    user_agent: str = "python-urllib",
) -> dict:
    """
    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param int timeout: Socket timeout in seconds
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    url = f"https://ipapi.co/{ip_address}/json/"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.load(response)
        if not data.get("reserved", False):
            return data
    raise CouldNotGeolocate


def geolocate_ipinfo_lite(
    ip_address: str = "",
    timeout: int = 2,
    user_agent: str = "python-urllib",
) -> dict:
    """
    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param int timeout: Socket timeout in seconds
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    url = f"https://ipinfo.io/{ip_address}/json"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)
    raise CouldNotGeolocate


def geolocate_findip_net(
    ip_address: str = "",
    timeout: int = 2,
    user_agent: str = "python-urllib",
) -> dict:
    """
    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param int timeout: Socket timeout in seconds
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    url = f"https://findip.net/{ip_address}.json"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)
    raise CouldNotGeolocate


# Default provider tuple
_GEO_FUNCS = (
    # geolocate_ip_api_com,  # This one is only http, not https.
    geolocate_ipwhois_io,
    geolocate_ipapi_co,
    geolocate_ipinfo_lite,
    geolocate_findip_net,
)

_COMMON_KEYS = {"ip", "city", "region", "country", "latitude", "longitude"}


def _try_providers(
    ip_address: str = "",
    timeout: int = 2,
    user_agent: str = "python-urllib",
    providers=_GEO_FUNCS,
) -> dict:
    funcs = list(providers)
    random.shuffle(funcs)
    last_exception: Exception | None = None
    for func in funcs:
        try:
            result = func(ip_address, timeout=timeout, user_agent=user_agent)
            if result:
                return result
        except Exception as exc:
            last_exception = exc
    if last_exception:
        raise last_exception
    raise RuntimeError("All geolocation providers returned empty results")


def whereismyip_dict(
    ip_address: str = "",
    timeout: int = 2,
    attempts: int = 2,
    user_agent: str = "python-urllib",
    providers=_GEO_FUNCS,
) -> dict:
    """
    Returns a limited set of common fields from the first successful geolocation provider.

    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param int timeout: Socket timeout in seconds
    :param int attempts: Total number of attempts to try providers
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    last_exception: Exception | None = None
    for _ in range(attempts):
        try:
            data = _try_providers(
                ip_address, timeout=timeout, user_agent=user_agent, providers=providers
            )
            # Return only the common keys
            return {k: data.get(k) for k in _COMMON_KEYS}
        except Exception as exc:
            last_exception = exc
    # If all attempts failed, re-raise the last exception
    raise last_exception


def whereismyip(
    ip_address: str = "",
    timeout: int = 2,
    attempts: int = 2,
    user_agent: str = "python-urllib",
    providers=_GEO_FUNCS,
) -> str:
    """
    Returns '<city>, <region>, <country>'.

    :param str ip_address: IPv4 or IPv6 address. If blank, whatismyip uses your public ip address.
    :param int timeout: Socket timeout in seconds
    :param int attempts: Total number of attempts to try providers
    :param str user_agent: Value to use for the User-Agent HTTP header
    """
    ip_address = _get_my_ip_if_needed(ip_address)
    last_exception: Exception | None = None
    for _ in range(attempts):
        try:
            data = _try_providers(
                ip_address,
                timeout=timeout,
                user_agent=user_agent,
                providers=providers,
            )
            break
        except Exception as exc:
            last_exception = exc
    else:
        raise last_exception

    city = data.get("city", "")
    region = data.get("region", data.get("regionName", ""))
    country = data.get("country", "")
    return ", ".join(filter(None, (city, region, country)))
