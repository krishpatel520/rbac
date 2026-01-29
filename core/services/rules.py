from typing import Callable, Dict, Any

Rule = Callable[[Any, Any], bool]
RULES: Dict[str, Rule] = {}


def rule(permission_code: str):
    def decorator(func: Rule):
        RULES[permission_code] = func
        return func
    return decorator


def evaluate_rule(permission_code: str, user, obj) -> bool:
    rule_fn = RULES.get(permission_code)
    if not rule_fn:
        return True
    return bool(rule_fn(user, obj))


def is_allowed(user, permission_code: str, obj=None) -> bool:
    return evaluate_rule(permission_code, user, obj)


from enquiry.models import EnquiryStatus
from followup.models import FollowUpStatus
from quotation.models import QuotationStatus
from organization.models import OrganizationStatus


# ─────────────────────────────
# ENQUIRY RULES
# ─────────────────────────────

@rule("enquiry.update")
def enquiry_update(user, enquiry):
    if enquiry is None:
        return True
    return enquiry.status in {
        EnquiryStatus.NEW,
        EnquiryStatus.QUALIFIED,
    }


@rule("enquiry.qualify")
def enquiry_qualify(user, enquiry):
    if enquiry is None:
        return True
    return enquiry.status == EnquiryStatus.NEW


@rule("enquiry.disqualify")
def enquiry_disqualify(user, enquiry):
    if enquiry is None:
        return True
    return enquiry.status == EnquiryStatus.NEW


@rule("enquiry.close")
def enquiry_close(user, enquiry):
    if enquiry is None:
        return True
    return enquiry.status == EnquiryStatus.QUALIFIED


# ─────────────────────────────
# FOLLOW-UP RULES
# ─────────────────────────────

@rule("followup.update")
def followup_update(user, followup):
    if followup is None:
        return True
    return followup.status == FollowUpStatus.PENDING


@rule("followup.complete")
def followup_complete(user, followup):
    if followup is None:
        return True
    return followup.status == FollowUpStatus.PENDING


@rule("followup.cancel")
def followup_cancel(user, followup):
    if followup is None:
        return True
    return followup.status == FollowUpStatus.PENDING


# ─────────────────────────────
# QUOTATION RULES
# ─────────────────────────────

@rule("quotation.update")
def quotation_update(user, quotation):
    if quotation is None:
        return True
    return quotation.status in {
        QuotationStatus.DRAFT,
        QuotationStatus.SENT,
    }


@rule("quotation.send")
def quotation_send(user, quotation):
    if quotation is None:
        return True
    return quotation.status == QuotationStatus.DRAFT


@rule("quotation.accept")
def quotation_accept(user, quotation):
    if quotation is None:
        return True
    return quotation.status == QuotationStatus.SENT


@rule("quotation.reject")
def quotation_reject(user, quotation):
    if quotation is None:
        return True
    return quotation.status == QuotationStatus.SENT


@rule("quotation.expire")
def quotation_expire(user, quotation):
    if quotation is None:
        return True
    return quotation.status == QuotationStatus.SENT


# ─────────────────────────────
# ORGANIZATION RULES
# ─────────────────────────────

@rule("organization.update")
def organization_update(user, org):
    if org is None:
        return True
    return org.status == OrganizationStatus.ACTIVE


@rule("organization.suspend")
def organization_suspend(user, org):
    if org is None:
        return True
    return org.status == OrganizationStatus.ACTIVE


@rule("organization.activate")
def organization_activate(user, org):
    if org is None:
        return True
    return org.status == OrganizationStatus.SUSPENDED


@rule("organization.archive")
def organization_archive(user, org):
    if org is None:
        return True
    return org.status != OrganizationStatus.ARCHIVED
