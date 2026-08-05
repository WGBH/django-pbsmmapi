from datetime import (
    UTC,
    datetime,
)


def parse_changelog_timestamp(timestamp: str) -> datetime:
    """Parse a changelog ISO timestamp string into an aware UTC datetime.

    Any offset in the string is normalized to UTC; a timestamp with no
    timezone is assumed to be UTC (not the local zone).
    """
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def time_zone_aware_now():
    """
    This just sends back a time zone aware "now()" with UTC as the time zone.
    """
    return datetime.now(UTC)
