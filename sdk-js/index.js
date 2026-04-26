const fetch = require("node-fetch");

class DriftWatch {
  constructor(baseUrl = "https://drift-watch.onrender.com") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async _request(method, path, body = null, params = null) {
    let url = `${this.baseUrl}${path}`;
    if (params) {
      const qs = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v != null)
      ).toString();
      if (qs) url += `?${qs}`;
    }
    const options = { method, headers: { "Content-Type": "application/json" } };
    if (body) options.body = JSON.stringify(body);
    const res = await fetch(url, options);
    if (!res.ok) throw new Error(`DriftWatch error: ${res.status} ${await res.text()}`);
    return res.json();
  }

  // Anchors
  createAnchor(domain, question, expectedContains, sourceUrl = null, verifiedAt = null, contributedBy = null) {
    return this._request("POST", "/anchors", {
      domain, question, expected_contains: expectedContains,
      source_url: sourceUrl, verified_at: verifiedAt, contributed_by: contributedBy
    });
  }
  listAnchors(domain = null) { return this._request("GET", "/anchors", null, { domain }); }
  getAnchor(anchorId) { return this._request("GET", `/anchors/${anchorId}`); }
  updateAnchor(anchorId, data) { return this._request("PUT", `/anchors/${anchorId}`, data); }
  deactivateAnchor(anchorId) { return this._request("DELETE", `/anchors/${anchorId}`); }

  // Endpoints
  createEndpoint(name, url, owner = null) { return this._request("POST", "/endpoints", { name, url, owner }); }
  listEndpoints() { return this._request("GET", "/endpoints"); }
  getEndpoint(endpointId) { return this._request("GET", `/endpoints/${endpointId}`); }
  deleteEndpoint(endpointId) { return this._request("DELETE", `/endpoints/${endpointId}`); }

  // Drift Checks
  runCheck(endpointId, domain = null) { return this._request("POST", "/check", { endpoint_id: endpointId, domain }); }
  listChecks(endpointId = null) { return this._request("GET", "/checks", null, { endpoint_id: endpointId }); }
  getCheck(checkId) { return this._request("GET", `/checks/${checkId}`); }
  getStaleness(endpointId, domain = null) { return this._request("GET", `/endpoints/${endpointId}/staleness`, null, { domain }); }

  // Utils
  stats() { return this._request("GET", "/dashboard/stats"); }
  health() { return this._request("GET", "/health"); }
}

module.exports = DriftWatch;