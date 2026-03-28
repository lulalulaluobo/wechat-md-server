from __future__ import annotations

import argparse
import sys
from secrets import token_urlsafe

from app.config import reset_admin_credentials


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reset wechat-md-server admin credentials")
    parser.add_argument("--username", help="Optional new admin username")
    parser.add_argument("--password", help="Explicit new admin password")
    parser.add_argument("--random", action="store_true", help="Generate a random new admin password")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.password and args.random:
        print("cannot use --password and --random together", file=sys.stderr)
        return 2
    if not args.password and not args.random:
        print("must provide --password or --random", file=sys.stderr)
        return 2

    password = args.password or token_urlsafe(16)
    updated = reset_admin_credentials(new_password=password, username=args.username)
    username = updated["auth"]["user"]["username"]

    print("password reset successful")
    print(f"username: {username}")
    if args.random:
        print(f"generated password: {password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
