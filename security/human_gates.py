"""Execution-boundary human gates. Ungated actions still need normal policy checks."""
from security.shape import ShapeError, State

HUMAN_GATED_ACTIONS = frozenset({
    "production-deploy", "credentials-access", "destructive-edit", "financial-action",
    "external-publication", "legal-filing", "irreversible-migration",
    "permission-escalation", "agent-creation", "policy-modification", "evidence-deletion",
    "security-control-disable", "bulk-data-export", "biometric-enrollment",
})


def is_gated(action):
    return action in HUMAN_GATED_ACTIONS


def enforce_human_gate(authorization, action, *, service=None, approval_id=None,
                       requester_id=None, resource=None, arguments=None):
    if not authorization.can_execute():
        raise ShapeError("Unapproved, expired or revoked authorization")
    if not is_gated(action):
        return
    if not authorization.history or authorization.history[-1].from_state != State.PENDING_HUMAN_APPROVAL or authorization.history[-1].to_state != State.APPROVED:
        raise ShapeError("Latest approval must follow human-pending state")
    if service is None or not approval_id:
        raise ShapeError("Trusted approval service and approval required")
    approver = service.consume(approval_id, request_id=authorization.request_id,
                               requester_id=requester_id, action=action,
                               resource=resource, arguments=arguments)
    return approver
