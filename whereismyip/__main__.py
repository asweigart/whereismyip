import sys

from . import CouldNotGeolocate, WhatIsMyIPPackageNotInstalled, whereismyip


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] in ("-h", "--help"):
        print("usage: whereismyip [IP_ADDRESS]", file=sys.stderr)
        return 0
    if len(argv) > 1:
        print("usage: whereismyip [IP_ADDRESS]", file=sys.stderr)
        return 2
    ip = argv[0] if argv else ""
    try:
        print(whereismyip(ip))
    except (CouldNotGeolocate, WhatIsMyIPPackageNotInstalled, ValueError) as exc:
        print(f"whereismyip: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
