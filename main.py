from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

app = FastAPI(
    title="DriftWatch",
    description="Semantic drift and model staleness monitor. Know when your model no longer knows what is true.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def db():
    return httpx.Client(base_url=f"{SUPABASE_URL}/rest/v1", headers=HEADERS, timeout=30.0)


# ─── Pydantic Models ───────────────────────────────────────────────────────────

class AnchorCreate(BaseModel):
    domain: str
    question: str
    expected_contains: str
    source_url: Optional[str] = None
    verified_at: Optional[str] = None
    contributed_by: Optional[str] = None

class AnchorUpdate(BaseModel):
    domain: Optional[str] = None
    question: Optional[str] = None
    expected_contains: Optional[str] = None
    source_url: Optional[str] = None
    verified_at: Optional[str] = None

class EndpointCreate(BaseModel):
    name: str
    url: str
    owner: Optional[str] = None

class CheckRequest(BaseModel):
    endpoint_id: str
    domain: Optional[str] = None


# ─── Status ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "tool": "DriftWatch",
        "version": "0.1.0",
        "status": "running",
        "description": "Semantic drift and model staleness monitor. Know when your model no longer knows what is true."
    }


@app.get("/health")
def health():
    try:
        with db() as client:
            client.get("/fact_anchors", params={"limit": "1"})
            return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


# ─── Fact Anchors ──────────────────────────────────────────────────────────────

@app.post("/anchors")
def create_anchor(body: AnchorCreate):
    with db() as client:
        r = client.post("/fact_anchors", json={
            "domain": body.domain,
            "question": body.question,
            "expected_contains": body.expected_contains,
            "source_url": body.source_url,
            "verified_at": body.verified_at,
            "contributed_by": body.contributed_by,
            "active": True
        })
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=r.text)
        return r.json()[0]


@app.get("/anchors")
def list_anchors(domain: Optional[str] = Query(default=None)):
    with db() as client:
        params = {"active": "eq.true", "order": "created_at.desc"}
        if domain:
            params["domain"] = f"eq.{domain}"
        r = client.get("/fact_anchors", params=params)
        return r.json()


@app.get("/anchors/{anchor_id}")
def get_anchor(anchor_id: str):
    with db() as client:
        r = client.get("/fact_anchors", params={"id": f"eq.{anchor_id}"})
        data = r.json()
        if not data:
            raise HTTPException(status_code=404, detail="Anchor not found")
        return data[0]


@app.put("/anchors/{anchor_id}")
def update_anchor(anchor_id: str, body: AnchorUpdate):
    update_data = {k: v for k, v in body.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    with db() as client:
        r = client.patch(
            "/fact_anchors",
            params={"id": f"eq.{anchor_id}"},
            json=update_data
        )
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=r.text)
        result = r.json()
        if not result:
            raise HTTPException(status_code=404, detail="Anchor not found")
        return result[0]


@app.delete("/anchors/{anchor_id}")
def deactivate_anchor(anchor_id: str):
    with db() as client:
        client.patch(
            "/fact_anchors",
            params={"id": f"eq.{anchor_id}"},
            json={"active": False}
        )
        return {"deactivated": True, "anchor_id": anchor_id}


# ─── Model Endpoints ───────────────────────────────────────────────────────────

@app.post("/endpoints")
def create_endpoint(body: EndpointCreate):
    with db() as client:
        r = client.post("/model_endpoints", json={
            "name": body.name,
            "url": body.url,
            "owner": body.owner
        })
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=r.text)
        return r.json()[0]


@app.get("/endpoints")
def list_endpoints():
    with db() as client:
        r = client.get("/model_endpoints", params={"order": "created_at.desc"})
        return r.json()


@app.get("/endpoints/{endpoint_id}")
def get_endpoint(endpoint_id: str):
    with db() as client:
        r = client.get("/model_endpoints", params={"id": f"eq.{endpoint_id}"})
        data = r.json()
        if not data:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        return data[0]


@app.delete("/endpoints/{endpoint_id}")
def delete_endpoint(endpoint_id: str):
    with db() as client:
        client.delete("/model_endpoints", params={"id": f"eq.{endpoint_id}"})
        return {"deleted": True, "endpoint_id": endpoint_id}


# ─── Drift Check Engine ────────────────────────────────────────────────────────

def call_model(url: str, question: str) -> str:
    """POST question to registered model endpoint. Extracts text from common response shapes."""
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(url, json={"input": question})
            r.raise_for_status()
            data = r.json()
            for field in ["output", "response", "result", "answer", "text", "content"]:
                if field in data:
                    return str(data[field])
            if isinstance(data, str):
                return data
            return json.dumps(data)
    except Exception as e:
        return f"[Error: {str(e)}]"


@app.post("/check")
def run_check(body: CheckRequest):
    with db() as client:
        # Verify endpoint exists
        ep_r = client.get("/model_endpoints", params={"id": f"eq.{body.endpoint_id}"})
        endpoints = ep_r.json()
        if not endpoints:
            raise HTTPException(status_code=404, detail="Endpoint not found")
        endpoint = endpoints[0]

        # Fetch active anchors, optionally filtered by domain
        anchor_params = {"active": "eq.true", "order": "created_at.asc"}
        if body.domain:
            anchor_params["domain"] = f"eq.{body.domain}"
        anchors_r = client.get("/fact_anchors", params=anchor_params)
        anchors = anchors_r.json()

        if not anchors:
            raise HTTPException(
                status_code=400,
                detail="No active anchors found. Create fact anchors first via POST /anchors."
            )

        # Create drift_check record — update with final numbers after all runs
        check_r = client.post("/drift_checks", json={
            "endpoint_id": body.endpoint_id,
            "domain": body.domain,
            "total_anchors": len(anchors),
            "passed": 0,
            "failed": 0,
            "staleness_score": 1.0,
            "drift_detected": False
        })
        if check_r.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=check_r.text)
        check_id = check_r.json()[0]["id"]

        passed_count = 0
        failed_count = 0
        any_drift = False
        results = []

        for anchor in anchors:
            anchor_id = anchor["id"]

            # Get most recent result for this anchor + endpoint pair
            prev_r = client.get("/drift_results", params={
                "anchor_id": f"eq.{anchor_id}",
                "endpoint_id": f"eq.{body.endpoint_id}",
                "order": "created_at.desc",
                "limit": "1"
            })
            prev_list = prev_r.json()
            previous_passed = prev_list[0]["passed"] if prev_list else None

            # Call the model
            actual_output = call_model(endpoint["url"], anchor["question"])

            # Pass/fail — case-insensitive substring match
            passed = anchor["expected_contains"].lower() in actual_output.lower()

            # Drift: previously passed this anchor, now failing it
            drift_detected = (previous_passed is True) and (not passed)
            if drift_detected:
                any_drift = True

            if passed:
                passed_count += 1
            else:
                failed_count += 1

            # Store result
            client.post("/drift_results", json={
                "check_id": check_id,
                "anchor_id": anchor_id,
                "endpoint_id": body.endpoint_id,
                "passed": passed,
                "actual_output": actual_output[:2000],
                "drift_detected": drift_detected
            })

            results.append({
                "anchor_id": anchor_id,
                "domain": anchor["domain"],
                "question": anchor["question"],
                "expected_contains": anchor["expected_contains"],
                "actual_output": actual_output[:500],
                "passed": passed,
                "drift_detected": drift_detected,
                "previously_passed": previous_passed
            })

        staleness_score = round(passed_count / len(anchors), 4) if anchors else 1.0

        # Update check record with final numbers
        client.patch(
            "/drift_checks",
            params={"id": f"eq.{check_id}"},
            json={
                "passed": passed_count,
                "failed": failed_count,
                "staleness_score": staleness_score,
                "drift_detected": any_drift
            }
        )

        return {
            "check_id": check_id,
            "endpoint_id": body.endpoint_id,
            "endpoint_name": endpoint["name"],
            "domain": body.domain,
            "total_anchors": len(anchors),
            "passed": passed_count,
            "failed": failed_count,
            "staleness_score": staleness_score,
            "drift_detected": any_drift,
            "results": results
        }


# ─── Check History ─────────────────────────────────────────────────────────────

@app.get("/checks")
def list_checks(endpoint_id: Optional[str] = Query(default=None)):
    with db() as client:
        params = {"order": "run_at.desc", "limit": "50"}
        if endpoint_id:
            params["endpoint_id"] = f"eq.{endpoint_id}"
        r = client.get("/drift_checks", params=params)
        return r.json()


@app.get("/checks/{check_id}")
def get_check(check_id: str):
    with db() as client:
        check_r = client.get("/drift_checks", params={"id": f"eq.{check_id}"})
        checks = check_r.json()
        if not checks:
            raise HTTPException(status_code=404, detail="Check not found")
        check = checks[0]

        results_r = client.get("/drift_results", params={
            "check_id": f"eq.{check_id}",
            "order": "created_at.asc"
        })
        results = results_r.json()

        # Enrich each result with its anchor's question and metadata
        enriched = []
        for res in results:
            anchor_r = client.get("/fact_anchors", params={"id": f"eq.{res['anchor_id']}"})
            anchor_data = anchor_r.json()
            anchor = anchor_data[0] if anchor_data else {}
            enriched.append({
                **res,
                "question": anchor.get("question"),
                "expected_contains": anchor.get("expected_contains"),
                "domain": anchor.get("domain"),
                "source_url": anchor.get("source_url")
            })

        return {**check, "results": enriched}


@app.get("/endpoints/{endpoint_id}/staleness")
def get_staleness(endpoint_id: str, domain: Optional[str] = Query(default=None)):
    with db() as client:
        params = {
            "endpoint_id": f"eq.{endpoint_id}",
            "order": "run_at.desc",
            "limit": "1"
        }
        if domain:
            params["domain"] = f"eq.{domain}"

        r = client.get("/drift_checks", params=params)
        checks = r.json()

        if not checks:
            return {
                "endpoint_id": endpoint_id,
                "domain": domain,
                "staleness_score": None,
                "message": "No checks run yet for this endpoint"
            }

        latest = checks[0]

        # Trend — last 10 checks for decay curve
        trend_params = {
            "endpoint_id": f"eq.{endpoint_id}",
            "order": "run_at.desc",
            "limit": "10",
            "select": "staleness_score,run_at,drift_detected,passed,failed,total_anchors,domain"
        }
        if domain:
            trend_params["domain"] = f"eq.{domain}"
        trend_r = client.get("/drift_checks", params=trend_params)
        trend = trend_r.json()

        return {
            "endpoint_id": endpoint_id,
            "domain": domain,
            "staleness_score": latest["staleness_score"],
            "drift_detected": latest["drift_detected"],
            "last_checked": latest["run_at"],
            "total_anchors": latest["total_anchors"],
            "passed": latest["passed"],
            "failed": latest["failed"],
            "trend": trend
        }


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/dashboard/stats")
def dashboard_stats():
    with db() as client:
        anchors_r = client.get("/fact_anchors", params={"active": "eq.true"})
        anchors = anchors_r.json()

        endpoints_r = client.get("/model_endpoints")
        endpoints = endpoints_r.json()

        checks_r = client.get("/drift_checks", params={"order": "run_at.desc", "limit": "100"})
        checks = checks_r.json()

        drift_events = sum(1 for c in checks if c.get("drift_detected"))
        scored = [c["staleness_score"] for c in checks if c.get("staleness_score") is not None]
        avg_staleness = round(sum(scored) / len(scored), 4) if scored else 1.0
        domains = list(set(a["domain"] for a in anchors))

        return {
            "total_anchors": len(anchors),
            "total_endpoints": len(endpoints),
            "total_checks": len(checks),
            "drift_events": drift_events,
            "avg_staleness_score": avg_staleness,
            "domains": domains,
            "recent_checks": checks[:10]
        }