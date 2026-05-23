import io
import json
import time
import unittest
from unittest.mock import patch, MagicMock

import whereismyip


def _mock_urlopen(payload):
    """Return a urlopen mock that yields a context manager wrapping JSON bytes."""
    body = io.BytesIO(json.dumps(payload).encode("utf-8"))
    cm = MagicMock()
    cm.__enter__.return_value = body
    cm.__exit__.return_value = False
    return MagicMock(return_value=cm)


class TestIPValidation(unittest.TestCase):
    def test_invalid_ip_raises_value_error(self):
        with self.assertRaises(ValueError):
            whereismyip.geolocate_ipwhois_io("not-an-ip")

    def test_path_traversal_attempt_rejected(self):
        with self.assertRaises(ValueError):
            whereismyip.geolocate_ipwhois_io("8.8.8.8/../admin")


class TestProviderParsing(unittest.TestCase):
    def test_ipwhois_io_success(self):
        payload = {
            "ip": "8.8.8.8",
            "success": True,
            "city": "Mountain View",
            "region": "California",
            "country": "United States",
            "country_code": "US",
            "latitude": 37.386,
            "longitude": -122.0838,
        }
        with patch("urllib.request.urlopen", _mock_urlopen(payload)):
            data = whereismyip.geolocate_ipwhois_io("8.8.8.8")
        self.assertEqual(data["ip"], "8.8.8.8")
        normalized = whereismyip._normalize_ipwhois_io(data)
        self.assertEqual(normalized["country"], "United States")
        self.assertEqual(normalized["country_code"], "US")

    def test_ipwhois_io_missing_ip_field_raises(self):
        with patch("urllib.request.urlopen", _mock_urlopen({"success": False})):
            with self.assertRaises(whereismyip.CouldNotGeolocate):
                whereismyip.geolocate_ipwhois_io("8.8.8.8")

    def test_ipapi_co_error_field_raises(self):
        with patch("urllib.request.urlopen", _mock_urlopen({"error": True, "reason": "RateLimited"})):
            with self.assertRaises(whereismyip.CouldNotGeolocate):
                whereismyip.geolocate_ipapi_co("8.8.8.8")

    def test_ipapi_co_normalize_uses_country_name(self):
        data = {
            "ip": "8.8.8.8",
            "city": "Mountain View",
            "region": "California",
            "country": "US",
            "country_name": "United States",
            "latitude": 37.386,
            "longitude": -122.0838,
        }
        normalized = whereismyip._normalize_ipapi_co(data)
        self.assertEqual(normalized["country"], "United States")
        self.assertEqual(normalized["country_code"], "US")

    def test_ipinfo_lite_splits_loc(self):
        data = {
            "ip": "8.8.8.8",
            "city": "Mountain View",
            "region": "California",
            "country": "US",
            "loc": "37.4056,-122.0775",
        }
        normalized = whereismyip._normalize_ipinfo_lite(data)
        self.assertAlmostEqual(normalized["latitude"], 37.4056)
        self.assertAlmostEqual(normalized["longitude"], -122.0775)
        self.assertEqual(normalized["country"], "United States")
        self.assertEqual(normalized["country_code"], "US")

    def test_ipinfo_lite_missing_loc_returns_none(self):
        data = {"ip": "8.8.8.8", "city": "X", "region": "Y", "country": "US"}
        normalized = whereismyip._normalize_ipinfo_lite(data)
        self.assertIsNone(normalized["latitude"])
        self.assertIsNone(normalized["longitude"])

    def test_findip_net_nested_structure(self):
        data = {
            "traits": {"ip_address": "8.8.8.8"},
            "city": {"names": {"en": "Mountain View"}},
            "country": {"iso_code": "US", "names": {"en": "United States"}},
            "subdivisions": [{"names": {"en": "California"}}],
            "location": {"latitude": 37.4, "longitude": -122.1},
        }
        normalized = whereismyip._normalize_findip_net(data)
        self.assertEqual(normalized["ip"], "8.8.8.8")
        self.assertEqual(normalized["city"], "Mountain View")
        self.assertEqual(normalized["region"], "California")
        self.assertEqual(normalized["country"], "United States")
        self.assertEqual(normalized["country_code"], "US")
        self.assertEqual(normalized["latitude"], 37.4)

    def test_findip_net_missing_traits_raises(self):
        with patch("urllib.request.urlopen", _mock_urlopen({"country": {}})):
            with self.assertRaises(whereismyip.CouldNotGeolocate):
                whereismyip.geolocate_findip_net("8.8.8.8")


class TestRetryAndAggregation(unittest.TestCase):
    def setUp(self):
        whereismyip.clear_cache()

    def test_attempts_must_be_positive(self):
        with self.assertRaises(ValueError):
            whereismyip.whereismyip_dict("8.8.8.8", attempts=0, cache_ttl=0)

    def test_all_providers_fail_raises_with_context(self):
        def boom(*a, **kw):
            raise RuntimeError("nope")

        providers = (boom, boom)
        with self.assertRaises(whereismyip.CouldNotGeolocate) as ctx:
            whereismyip.whereismyip_dict(
                "8.8.8.8", attempts=1, providers=providers, cache_ttl=0
            )
        msg = str(ctx.exception)
        self.assertIn("boom", msg)
        self.assertIn("nope", msg)

    def test_first_success_short_circuits(self):
        def fail(*a, **kw):
            raise RuntimeError("down")

        def ok(*a, **kw):
            return {"ip": "8.8.8.8", "city": "X", "region": "Y", "country": "Z"}

        result = whereismyip.whereismyip_dict(
            "8.8.8.8", attempts=1, providers=(fail, ok), cache_ttl=0
        )
        self.assertEqual(result["ip"], "8.8.8.8")

    def test_whereismyip_string_format(self):
        def ok(*a, **kw):
            return {
                "ip": "8.8.8.8",
                "city": "Mountain View",
                "region": "California",
                "country": "United States",
            }

        result = whereismyip.whereismyip(
            "8.8.8.8", attempts=1, providers=(ok,), cache_ttl=0
        )
        self.assertEqual(result, "Mountain View, California, United States")


class TestCache(unittest.TestCase):
    def setUp(self):
        whereismyip.clear_cache()

    def test_repeat_call_within_ttl_skips_network(self):
        call_count = {"n": 0}

        def counting(*a, **kw):
            call_count["n"] += 1
            return {"ip": "8.8.8.8", "city": "X", "region": "Y", "country": "Z"}

        providers = (counting,)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        self.assertEqual(call_count["n"], 1)

    def test_different_ip_addresses_dont_collide(self):
        call_count = {"n": 0}

        def counting(ip_address="", **kw):
            call_count["n"] += 1
            return {"ip": ip_address, "city": "X", "region": "Y", "country": "Z"}

        providers = (counting,)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        whereismyip.whereismyip_dict("1.1.1.1", attempts=1, providers=providers)
        self.assertEqual(call_count["n"], 2)

    def test_cache_ttl_zero_bypasses_cache(self):
        call_count = {"n": 0}

        def counting(*a, **kw):
            call_count["n"] += 1
            return {"ip": "8.8.8.8", "city": "X", "region": "Y", "country": "Z"}

        providers = (counting,)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers, cache_ttl=0)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers, cache_ttl=0)
        self.assertEqual(call_count["n"], 2)

    def test_clear_cache_forces_refresh(self):
        call_count = {"n": 0}

        def counting(*a, **kw):
            call_count["n"] += 1
            return {"ip": "8.8.8.8", "city": "X", "region": "Y", "country": "Z"}

        providers = (counting,)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        whereismyip.clear_cache()
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        self.assertEqual(call_count["n"], 2)

    def test_expired_entry_triggers_refresh(self):
        call_count = {"n": 0}

        def counting(*a, **kw):
            call_count["n"] += 1
            return {"ip": "8.8.8.8", "city": "X", "region": "Y", "country": "Z"}

        providers = (counting,)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers, cache_ttl=0.05)
        time.sleep(0.1)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers, cache_ttl=0.05)
        self.assertEqual(call_count["n"], 2)

    def test_mutating_returned_dict_does_not_poison_cache(self):
        def ok(*a, **kw):
            return {"ip": "8.8.8.8", "city": "X", "region": "Y", "country": "Z"}

        providers = (ok,)
        first = whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        first["city"] = "MUTATED"
        second = whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        self.assertEqual(second["city"], "X")

    def test_whereismyip_shares_cache_with_dict(self):
        call_count = {"n": 0}

        def counting(*a, **kw):
            call_count["n"] += 1
            return {"ip": "8.8.8.8", "city": "X", "region": "Y", "country": "Z"}

        providers = (counting,)
        whereismyip.whereismyip_dict("8.8.8.8", attempts=1, providers=providers)
        whereismyip.whereismyip("8.8.8.8", attempts=1, providers=providers)
        self.assertEqual(call_count["n"], 1)


class TestGetMyIpIfNeeded(unittest.TestCase):
    def test_passes_through_provided_ip(self):
        self.assertEqual(whereismyip._get_my_ip_if_needed("1.2.3.4"), "1.2.3.4")

    def test_missing_whatismyip_raises(self):
        with patch.object(whereismyip, "_HAS_WHATISMYIP", False):
            with self.assertRaises(whereismyip.WhatIsMyIPPackageNotInstalled):
                whereismyip._get_my_ip_if_needed("")


if __name__ == "__main__":
    unittest.main()
