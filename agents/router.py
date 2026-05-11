
from experts.report import generate_report
from experts.security import security_check
from experts.buddy import buddy_respond

def route_task(task):
    task_type = task.get("type", "report")

    if task_type == "security":
        return security_check(task)

    if task_type == "buddy":
        return buddy_respond(task)

    return generate_report(task)