# whereismyip
An IP address geolocation module for Python 3 that only uses the standard library (and the whatismyip package) and free, no-registration geolocation services.

The package exposes two main convenience functions: `whereismyip(ip)` and `whereismyip_dict(ip)`

The IP address argument can be an IPv4 or IPv6 address. If this argument is not given, the [`whatismyip`](https://pypi.org/project/WhatIsMyIP/) package is used to determine your public IP address (also from free, no-registration services.) All geolocation services are free, don't require registration, and use HTTPS.



## Example

```python
>>> import whereismyip

>>> whereismyip.whereismyip()
'Bellevue, Washington, US'

>>> whereismyip.whereismyip_dict()
{'city': 'Bellevue', 'latitude': None, 'ip': '23.234.81.85', 'country': 'US', 'longitude': None, 'region': 'Washington'}

>>> whereismyip.whereismyip_dict()  # The geolocate service used is randomly selected, so replies may be different.
{'city': 'Portland', 'latitude': 45.5230622, 'ip': '23.234.81.85', 'country': 'United States', 'longitude': -122.6764816, 'region': 'Oregon'}

>>> whereismyip.whereismyip("8.8.8.8")
'Mountain View, California, United States'

>>> whereismyip.whereismyip_dict('8.8.8.8')
{'city': 'Mountain View', 'latitude': 37.3860517, 'ip': '8.8.8.8', 'country': 'United States', 'longitude': -122.0838511, 'region': 'California'}
```

## Reference

    def whereismyip(
        ip_address: str = "",
        timeout: int = 2,
        attempts: int = 2,
        user_agent: str = "python-urllib",
        providers=_GEO_FUNCS,
    ) -> str:

    def whereismyip_dict(
        ip_address: str = "",
        timeout: int = 2,
        attempts: int = 2,
        user_agent: str = "python-urllib",
        providers=_GEO_FUNCS,
    ) -> dict:

The four geolocation services are [ipwhois.io](https://ipwhois.io/), [ipapi.co](https://ipapi.co/), [IPinfo.io](https://ipinfo.io/), and [FindIP.net](https://findip.net/).

    def geolocate_ipwhois_io(
        ip_address: str = "",
        timeout: int = 2,
        user_agent: str = "python-urllib",
    ) -> dict:

    def geolocate_ipapi_co(
        ip_address: str = "",
        timeout: int = 2,
        user_agent: str = "python-urllib",
    ) -> dict:

    def geolocate_ipinfo_lite(
        ip_address: str = "",
        timeout: int = 2,
        user_agent: str = "python-urllib",
    ) -> dict:

    def geolocate_findip_net(
        ip_address: str = "",
        timeout: int = 2,
        user_agent: str = "python-urllib",
    ) -> dict:

