# DriftWatch Python SDK

`pip install thread-driftwatch`

```python
from driftwatch import DriftWatch
dw = DriftWatch()

endpoint = dw.create_endpoint("my-model", "https://my-model.com/run")
anchor = dw.create_anchor("tax-law", "What is the VAT rate in Ghana?", "15%", source_url="https://gra.gov.gh")
result = dw.run_check(endpoint["id"], domain="tax-law")

print(result["staleness_score"])   # 1.0 = fully current, 0.0 = fully stale
print(result["drift_detected"])    # True if a previously passing anchor now fails
```

Part of the [Thread Suite](https://github.com/eugene001dayne).