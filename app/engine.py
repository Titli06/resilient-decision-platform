import operator
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import random
from app.database import SessionLocal
from app.models import AuditLog

OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq}

class DecisionEngine:
    def __init__(self, config):
        self.config = config

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1), retry=retry_if_exception_type(Exception))
    def simulate_external_dependency(self):
        if random.random() < 0.3:  # 30% failure rate
            raise Exception("External service timeout (simulated)")
        return True

    def evaluate_rule(self, rule, data):
        field_val = data.get(rule["field"])
        if field_val is None:
            return False, f"Missing field: {rule['field']}"
        try:
            result = OPS[rule["op"]](field_val, rule["value"])
            return result, rule["explanation"] if not result else "Passed"
        except:
            return False, "Evaluation error"

    def run_workflow(self, request_id: str, workflow_id: str, data: dict):
        db = SessionLocal()
        workflow = self.config.get(workflow_id)
        if not workflow:
            return {"status": "error", "reason": "Unknown workflow"}

        trace = []
        status = "approved"

        for stage in workflow["stages"]:
            # Simulate external dep with retry
            if stage.get("external_dependency"):
                try:
                    self.simulate_external_dependency()
                except Exception as e:
                    trace.append({"stage": stage["name"], "result": "failed", "explanation": str(e)})
                    status = "manual_review"
                    self._log_audit(db, request_id, stage["name"], "external", "failed", str(e))
                    break

            # Evaluate rules
            stage_result = "approve"
            for rule in stage["rules"]:
                passed, explanation = self.evaluate_rule(rule, data)
                self._log_audit(db, request_id, stage["name"], str(rule), "pass" if passed else "fail", explanation)
                trace.append({"stage": stage["name"], "rule": rule, "passed": passed, "explanation": explanation})
                
                if not passed:
                    stage_result = rule["fail_action"]
                    if stage_result in ["reject", "manual_review"]:
                        status = stage_result
                        break
            if status != "approved":
                break

        # Save final state
        from app.models import Request
        req = db.query(Request).filter_by(id=request_id).first()
        if req:
            req.status = status
        db.commit()
        db.close()

        return {
            "request_id": request_id,
            "status": status,
            "trace": trace,
            "audit_explanation": f"Decision based on {len(trace)} rule evaluations with full audit trail."
        }

    def _log_audit(self, db, request_id, stage, rule, result, explanation):
        log = AuditLog(request_id=request_id, stage=stage, rule=str(rule), result=result, explanation=explanation)
        db.add(log)