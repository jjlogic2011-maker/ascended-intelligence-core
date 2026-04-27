
from experts.report import generate_report
from experts.security import security_check

def route_task(task):
    task_type = task.get("type", "report")

    if task_type == "security":
        return security_check(task)

    return generate_report(task)