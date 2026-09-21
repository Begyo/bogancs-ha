"""Constants for the Bogáncs kisállatkönyv integration."""

from datetime import timedelta

DOMAIN = "bogancs"

# The hosted service. A self-hosted instance can override this in the config flow,
# but the point of the integration is that the user only has to paste the key.
DEFAULT_URL = "https://app.kisallatkonyv.hu"

CONF_KEY = "api_key"
CONF_URL = "url"

# The server recomputes today's doses on every request; a minute is frequent enough
# for a schedule that is measured in hours, and gentle on a small self-hosted box.
UPDATE_INTERVAL = timedelta(seconds=60)

# Endpoints
API_STATE = "/api/ha/state"
API_DOSE = "/api/ha/dose"
API_FEED = "/api/ha/feed"

ATTR_MEDICATION = "medication"
ATTR_SCHEDULED = "scheduled"
ATTR_GIVEN = "given"
ATTR_BY = "by"
ATTR_MISSED = "missed"
ATTR_REASON = "reason"

ATTR_FEEDING = "feeding"
ATTR_ALKALOM = "alkalom"
ATTR_FED = "fed"
ATTR_FEED_MISSED = "missed"

SERVICE_DOSE = "dose"
SERVICE_FEED = "feed"
