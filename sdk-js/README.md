# DriftWatch JavaScript SDK

`npm install thread-driftwatch`

Semantic drift and model staleness monitor for AI systems. Part of the [Thread Suite](https://github.com/eugene001dayne).

## Quick Start

```javascript
const DriftWatch = require("thread-driftwatch");
const dw = new DriftWatch(); // defaults to https://drift-watch.onrender.com

// Register your model endpoint
const endpoint = await dw.createEndpoint("my-model", "https://your-model.com/run");

// Define a ground truth anchor
const anchor = await dw.createAnchor(
  "tax-law-ghana",
  "What is the current VAT rate in Ghana?",
  "15%",
  "https://gra.gov.gh"
);

// Run a drift check
const result = await dw.runCheck(endpoint.id, "tax-law-ghana");

console.log(result.staleness_score);  // 1.0 = fully current, 0.0 = fully stale
console.log(result.drift_detected);   // true = a previously passing anchor is now failing
```

## Methods

### Fact Anchors
```javascript
dw.createAnchor(domain, question, expectedContains, sourceUrl, verifiedAt, contributedBy)
dw.listAnchors(domain)
dw.getAnchor(anchorId)
dw.updateAnchor(anchorId, data)
dw.deactivateAnchor(anchorId)
```

### Model Endpoints
```javascript
dw.createEndpoint(name, url, owner)
dw.listEndpoints()
dw.getEndpoint(endpointId)
dw.deleteEndpoint(endpointId)
```

### Drift Checks
```javascript
dw.runCheck(endpointId, domain)   // run all anchors against live endpoint
dw.listChecks(endpointId)         // check history
dw.getCheck(checkId)              // full check with per-anchor results
dw.getStaleness(endpointId, domain) // latest staleness score + trend
```

### Utils
```javascript
dw.stats()   // dashboard overview
dw.health()  // health check
```

## What It Detects

DriftWatch detects **semantic drift** — when an AI model that used to answer a question correctly starts getting it wrong. This happens silently when:

- Model providers push updates without notice
- Laws, regulations, or facts change after training cutoff
- Company policies or pricing change and the model doesn't know

## Links

- [Live API](https://drift-watch.onrender.com)
- [API Docs](https://drift-watch.onrender.com/docs)
- [GitHub](https://github.com/eugene001dayne/drift-watch)
- [Python SDK](https://pypi.org/project/thread-driftwatch/)
- [Thread Suite](https://github.com/eugene001dayne)