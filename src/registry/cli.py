import argparse
import json
import sys
from typing import List, Optional

from src.ingest.sources import ListingNotFound
from src.registry.dispatch import dispatcher_from_env
from src.registry.resolve import ResolveError, Resolver
from src.registry.service import ListingRequest, RegistrationRejected, RegistryService, app_to_dict
from src.store.errors import StoreError
from src.store.factory import open_store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m src.registry", description="Manage the registered apps (max 5)")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List registered apps")
    list_parser.add_argument("--include-archived", action="store_true")
    list_parser.add_argument("--keys", action="store_true", help="Print a JSON array of active app keys")

    search = sub.add_parser("search", help="Top 3 matches per store")
    search.add_argument("--name", required=True)
    search.add_argument("--country", default="in")

    add = sub.add_parser("add", help="Register confirmed listings and start the backfill")
    add.add_argument("--name", required=True, help="Display name")
    add.add_argument("--play", default=None, help="Play package name, e.g. com.nextbillion.groww")
    add.add_argument("--ios", default=None, help="App Store numeric ID, e.g. 1404871703")
    add.add_argument("--country", default="in")

    rename = sub.add_parser("rename", help="Change the display name only")
    rename.add_argument("--app", required=True)
    rename.add_argument("--name", required=True)

    archive = sub.add_parser("archive", help="Archive an app and free its slot")
    archive.add_argument("--app", required=True)
    return parser


def default_service() -> RegistryService:
    return RegistryService(open_store(), Resolver(), dispatcher_from_env())


def run(argv: Optional[List[str]] = None, service: Optional[RegistryService] = None) -> int:
    args = build_parser().parse_args(argv)
    service = service or default_service()
    try:
        if args.command == "list":
            apps = service.list_apps(include_archived=args.include_archived)
            if args.keys:
                print(json.dumps([a.app_key for a in apps if a.status != "archived"]))
            else:
                print(json.dumps({"slots_used": service.slots_used(), "apps": [app_to_dict(a) for a in apps]}, indent=2))
        elif args.command == "search":
            print(json.dumps(service.search(args.name, args.country).to_dict(), indent=2, ensure_ascii=False))
        elif args.command == "add":
            request = ListingRequest(args.name, args.play, args.ios, args.country)
            print(json.dumps(service.register(request).to_dict(), indent=2))
        elif args.command == "rename":
            print(json.dumps(app_to_dict(service.rename(args.app, args.name)), indent=2))
        elif args.command == "archive":
            print(json.dumps(app_to_dict(service.archive(args.app)), indent=2))
    except (StoreError, RegistrationRejected, ResolveError, ListingNotFound) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
