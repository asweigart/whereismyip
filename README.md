# whereismyip
An IP address geolocation module for Python 3 that only uses the standard library (and the whatismyip package) and free, no-registration geolocation services.

The package exposes two convenience functions, `whereismyip(ip)` and `whereismyip_dict(ip)`, plus a per-provider function for each supported geolocation service if you want to query one directly.

The IP address argument can be an IPv4 or IPv6 address. If this argument is not given, the [`whatismyip`](https://pypi.org/project/WhatIsMyIP/) package is used to determine your public IP address (also from free, no-registration services.) All geolocation services are free, don't require registration, and use HTTPS.



## Example

```python
>>> import whereismyip

>>> whereismyip.whereismyip()
'Bellevue, Washington, United States'

>>> whereismyip.whereismyip_dict()
{'ip': '23.234.81.85', 'city': 'Bellevue', 'region': 'Washington', 'country': 'United States', 'country_code': 'US', 'latitude': 47.6101, 'longitude': -122.2015}

>>> whereismyip.whereismyip_dict()  # The geolocate service used is randomly selected, so values may vary slightly.
{'ip': '23.234.81.85', 'city': 'Bellevue', 'region': 'Washington', 'country': 'United States', 'country_code': 'US', 'latitude': 47.5446, 'longitude': -122.1559}

>>> whereismyip.whereismyip("8.8.8.8")
'Mountain View, California, United States'

>>> whereismyip.whereismyip_dict('8.8.8.8')
{'ip': '8.8.8.8', 'city': 'Mountain View', 'region': 'California', 'country': 'United States', 'country_code': 'US', 'latitude': 37.3860517, 'longitude': -122.0838511}
```

Successful lookups are cached in-process for 2 seconds, so tight loops or repeated calls don't hammer the providers. Pass `cache_ttl=0` to bypass, or call `whereismyip.clear_cache()` to drop the cache.

## Command line

After installing, the `whereismyip` command is available on your PATH. It can also be run as a module:

```
$ whereismyip
Bellevue, Washington, United States

$ whereismyip 8.8.8.8
Mountain View, California, United States

$ python -m whereismyip 8.8.8.8
Mountain View, California, United States
```

Exit code is `0` on success, `1` on lookup failure, `2` on usage errors.

## Reference

    def whereismyip(
        ip_address: str = "",
        timeout: float = 2.0,
        attempts: int = 2,
        user_agent: str = _DEFAULT_USER_AGENT,
        providers=_GEO_FUNCS,
        cache_ttl: float = 2.0,
    ) -> str:

    def whereismyip_dict(
        ip_address: str = "",
        timeout: float = 2.0,
        attempts: int = 2,
        user_agent: str = _DEFAULT_USER_AGENT,
        providers=_GEO_FUNCS,
        cache_ttl: float = 2.0,
    ) -> dict:

    def clear_cache() -> None:

The four geolocation services are [ipwhois.io](https://ipwhois.io/), [ipapi.co](https://ipapi.co/), [IPinfo.io](https://ipinfo.io/), and [FindIP.net](https://findip.net/).

    def geolocate_ipwhois_io(
        ip_address: str = "",
        timeout: float = 2.0,
        user_agent: str = _DEFAULT_USER_AGENT,
    ) -> dict:

    def geolocate_ipapi_co(
        ip_address: str = "",
        timeout: float = 2.0,
        user_agent: str = _DEFAULT_USER_AGENT,
    ) -> dict:

    def geolocate_ipinfo_lite(
        ip_address: str = "",
        timeout: float = 2.0,
        user_agent: str = _DEFAULT_USER_AGENT,
    ) -> dict:

    def geolocate_findip_net(
        ip_address: str = "",
        timeout: float = 2.0,
        user_agent: str = _DEFAULT_USER_AGENT,
    ) -> dict:

