from app import config
from app.audit.audit_log import append_entry
from app.jira import client as jira_client
from app.protocol import signing
from app.schemas import ActionProposal


def _run_jira_action(proposal: ActionProposal) -> dict:
    fields = proposal.fields

    if proposal.action_type == "create_issue":
        issue_key = jira_client.create_issue(
            project_key=config.JIRA_PROJECT_KEY,
            issue_type=fields.get("issue_type", "Task"),
            summary=fields["summary"],
            description=fields.get("description", ""),
        )
        return {"issue_key": issue_key}

    if proposal.action_type == "transition_issue":
        jira_client.transition_issue(proposal.target_issue, fields["transition_name"])
        return {"issue_key": proposal.target_issue}

    if proposal.action_type == "add_comment":
        jira_client.add_comment(proposal.target_issue, fields["body"])
        return {"issue_key": proposal.target_issue}

    if proposal.action_type == "search":
        issues = jira_client.search_jql(fields["jql"], fields.get("max_results", 20))
        return {"issue_count": len(issues)}

    raise ValueError(f"Unsupported action_type: {proposal.action_type}")


def execute(token: str) -> dict:
    try:
        proposal = signing.verify_token(token)
    except signing.TokenError as error:
        append_entry({"token_error": str(error)}, "rejected")
        return {"status": "rejected", "error": str(error)}

    payload = {"action_proposal": proposal.model_dump()}

    try:
        result = _run_jira_action(proposal)
    except Exception as error:
        append_entry(payload, f"failure: {error}")
        return {"status": "failure", "error": str(error)}

    append_entry(payload, "success")
    return {"status": "success", **result}
