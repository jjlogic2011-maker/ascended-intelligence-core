from agents.router import route_task

class Orchestrator:

    def run(self, task):
        if not task:
            return {"error": "No task provided"}

        result = route_task(task)

        return {
            "status": "executed",
            "result": result
        }