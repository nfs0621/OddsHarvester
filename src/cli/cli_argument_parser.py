import argparse
from .cli_help_message_generator import CLIHelpMessageGenerator
from src.utils.sport_market_constants import Sport
from src.storage.storage_type import StorageType
from src.storage.storage_format import StorageFormat

class CLIArgumentParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="OddsHarvester CLI for scraping betting odds data.",
            epilog=CLIHelpMessageGenerator().generate(),
            formatter_class=argparse.RawTextHelpFormatter
        )
        self._initialize_subparsers()

    def _initialize_subparsers(self):
        subparsers = self.parser.add_subparsers(
            title="Commands", 
            dest="command",
            help="Specify whether you want to scrape upcoming matches or historical odds."
        )

        self._add_upcoming_parser(subparsers)
        self._add_historic_parser(subparsers)

    def _add_upcoming_parser(self, subparsers):
        parser = subparsers.add_parser("scrape_upcoming", help="Scrape odds for upcoming matches.")
        self._add_common_arguments(parser)
        parser.add_argument("--date", type=str, help="📅 Date for upcoming matches (format: YYYYMMDD).")

    def _add_historic_parser(self, subparsers):
        parser = subparsers.add_parser("scrape_historic", help="Scrape historical odds for a specific league and/or season.")
        self._add_common_arguments(parser)
        parser.add_argument("--season", type=str, required=True, help="📅 Season to scrape (format: YYYY-YYYY, e.g., 2022-2023).")
        parser.add_argument("--max_pages", type=int, help="📑 Maximum number of pages to scrape (optional).")

    def _add_common_arguments(self, parser):
        parser.add_argument(
            "--match_links",
            nargs="+",  # Allows multiple values
            type=str,
            default=None,
            help="🔗 Specific match links to scrape. Overrides sport, league, and date."
        )
        parser.add_argument(
            "--sport",
            type=str,
            choices=["football", "tennis", "basketball", "rugby-league", "baseball"],
            default="football",
            help="Specify the sport to scrape (e.g., football, tennis, basketball, rugby-league, baseball)."
        )
        parser.add_argument("--league", type=str, help="Specific league (e.g., premier-league).")
        parser.add_argument(
            "--markets",
            type=lambda s: s.split(','),
            help="💰 Comma-separated list of markets to scrape (e.g., 1x2,btts)."
        )
        parser.add_argument(
            "--storage",
            type=str,
            choices=[f.value for f in StorageType],
            default="local",
            help="💾 Storage type: local or remote (default: local)."
        )
        parser.add_argument("--file_path", type=str, help="File path for saving data.")
        parser.add_argument(
            "--format",
            type=str,
            choices=[f.value for f in StorageFormat],
            help="📝 Storage format (json or csv)."
        )
        parser.add_argument(
            "--proxies",
            nargs="+",
            default=None,
            help="🌐 List of proxies in 'server user pass' format (e.g., 'http://proxy.com:8080 user pass')."
        )
        parser.add_argument(
            "--browser_user_agent",
            type=str,
            default=None,
            help="🔍 Custom browser user agent (optional)."
        )
        parser.add_argument(
            "--browser_locale_timezone",
            type=str,
            default=None,
            help="🌍 Browser locale timezone (e.g., fr-BE) (optional)."
        )
        parser.add_argument(
            "--browser_timezone_id",
            type=str,
            default=None,
            help="⏰ Browser timezone ID (e.g., Europe/Brussels) (optional)."
        )
        parser.add_argument("--headless", action="store_true", help="🕶️ Run browser in headless mode.")
        parser.add_argument("--save_logs", action="store_true", help="📜 Save logs for debugging.")
        parser.add_argument(
            "--target_bookmaker",
            type=str,
            default=None,
            help="🎯 Specify a bookmaker name to only scrape data from that bookmaker."
        )
        parser.add_argument(
            "--scrape_odds_history",
            action="store_true",
            help="📈 Include to scrape historical odds movement (hover-over modal)."
        )

    def get_parser(self) -> argparse.ArgumentParser:
        return self.parser