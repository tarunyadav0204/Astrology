"""Chart Chat pricing; entitlement checks always use the server's active license."""
from credits.entitlements import ASTROLOGER_TOOLS_ENTITLEMENT, has_entitlement

SETTING = 'chart_chat_cost'
DEFAULT_COST = 2


def chart_chat_is_free(user):
    return has_entitlement(user, ASTROLOGER_TOOLS_ENTITLEMENT)


def chart_chat_cost(service, user):
    if chart_chat_is_free(user):
        return 0
    return service.get_effective_cost(user.userid, service.get_credit_setting(SETTING), SETTING)
