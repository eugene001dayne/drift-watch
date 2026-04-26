import httpx
from typing import Optional


class DriftWatch:
    def __init__(self, base_url: str = "https://drift-watch.onrender.com"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=60.0)

    # ── Anchors ──────────────────────────────────────────────────────────────

    def create_anchor(self, domain: str, question: str, expected_contains: str,
                      source_url: str = None, verified_at: str = None,
                      contributed_by: str = None):
        r = self.client.post("/anchors", json={
            "domain": domain,
            "question": question,
            "expected_contains": expected_contains,
            "source_url": source_url,
            "verified_at": verified_at,
            "contributed_by": contributed_by
        })
        r.raise_for_status()
        return r.json()

    def list_anchors(self, domain: str = None):
        params = {"domain": domain} if domain else {}
        r = self.client.get("/anchors", params=params)
        r.raise_for_status()
        return r.json()

    def get_anchor(self, anchor_id: str):
        r = self.client.get(f"/anchors/{anchor_id}")
        r.raise_for_status()
        return r.json()

    def update_anchor(self, anchor_id: str, **kwargs):
        r = self.client.put(f"/anchors/{anchor_id}", json=kwargs)
        r.raise_for_status()
        return r.json()

    def deactivate_anchor(self, anchor_id: str):
        r = self.client.delete(f"/anchors/{anchor_id}")
        r.raise_for_status()
        return r.json()

    # ── Model Endpoints ───────────────────────────────────────────────────────

    def create_endpoint(self, name: str, url: str, owner: str = None):
        r = self.client.post("/endpoints", json={"name": name, "url": url, "owner": owner})
        r.raise_for_status()
        return r.json()

    def list_endpoints(self):
        r = self.client.get("/endpoints")
        r.raise_for_status()
        return r.json()

    def get_endpoint(self, endpoint_id: str):
        r = self.client.get(f"/endpoints/{endpoint_id}")
        r.raise_for_status()
        return r.json()

    def delete_endpoint(self, endpoint_id: str):
        r = self.client.delete(f"/endpoints/{endpoint_id}")
        r.raise_for_status()
        return r.json()

    # ── Drift Checks ──────────────────────────────────────────────────────────

    def run_check(self, endpoint_id: str, domain: str = None):
        r = self.client.post("/check", json={"endpoint_id": endpoint_id, "domain": domain})
        r.raise_for_status()
        return r.json()

    def list_checks(self, endpoint_id: str = None):
        params = {"endpoint_id": endpoint_id} if endpoint_id else {}
        r = self.client.get("/checks", params=params)
        r.raise_for_status()
        return r.json()

    def get_check(self, check_id: str):
        r = self.client.get(f"/checks/{check_id}")
        r.raise_for_status()
        return r.json()

    def get_staleness(self, endpoint_id: str, domain: str = None):
        params = {"domain": domain} if domain else {}
        r = self.client.get(f"/endpoints/{endpoint_id}/staleness", params=params)
        r.raise_for_status()
        return r.json()

    # ── Utils ─────────────────────────────────────────────────────────────────

    def stats(self):
        r = self.client.get("/dashboard/stats")
        r.raise_for_status()
        return r.json()

    def health(self):
        r = self.client.get("/health")
        r.raise_for_status()
        return r.json()
    
    # ── Alerts ───────────────────────────────────────────────────────────────

    def list_alerts(self, endpoint_id: str = None, domain: str = None,
                    severity: str = None, resolved: bool = None):
        params = {}
        if endpoint_id:
            params["endpoint_id"] = endpoint_id
        if domain:
            params["domain"] = domain
        if severity:
            params["severity"] = severity
        if resolved is not None:
            params["resolved"] = resolved
        r = self.client.get("/alerts", params=params)
        r.raise_for_status()
        return r.json()

    def get_alert(self, alert_id: str):
        r = self.client.get(f"/alerts/{alert_id}")
        r.raise_for_status()
        return r.json()

    def resolve_alert(self, alert_id: str):
        r = self.client.patch(f"/alerts/{alert_id}/resolve")
        r.raise_for_status()
        return r.json()

    # ── Webhooks ─────────────────────────────────────────────────────────────

    def create_webhook(self, name: str, url: str,
                       on_drift: bool = True, min_severity: str = "high"):
        r = self.client.post("/webhooks", json={
            "name": name,
            "url": url,
            "on_drift": on_drift,
            "min_severity": min_severity
        })
        r.raise_for_status()
        return r.json()

    def list_webhooks(self):
        r = self.client.get("/webhooks")
        r.raise_for_status()
        return r.json()

    def delete_webhook(self, webhook_id: str):
        r = self.client.delete(f"/webhooks/{webhook_id}")
        r.raise_for_status()
        return r.json()