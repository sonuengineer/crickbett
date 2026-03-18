class CricketArbException(Exception):
    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ScraperError(CricketArbException):
    def __init__(self, bookmaker: str, message: str = "Scraping failed"):
        super().__init__(message=f"{bookmaker}: {message}", code="SCRAPER_ERROR")


class OddsStaleError(CricketArbException):
    def __init__(self, age_seconds: int):
        super().__init__(
            message=f"Odds are {age_seconds}s old, exceeds max age",
            code="ODDS_STALE",
        )


class MatchNotFoundError(CricketArbException):
    def __init__(self, match_id: str):
        super().__init__(message=f"Match {match_id} not found", code="MATCH_NOT_FOUND")


class BookmakerUnavailableError(CricketArbException):
    def __init__(self, bookmaker: str):
        super().__init__(
            message=f"{bookmaker} is currently unavailable",
            code="BOOKMAKER_UNAVAILABLE",
        )
