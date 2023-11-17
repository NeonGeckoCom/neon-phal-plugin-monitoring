# Core Monitoring Plugin
This plugin monitors messagebus traffic to log events and metrics. This data may
optionally be uploaded to a remote endpoint and/or saved locally for evaluation.

## Configuration
Metrics may be uploaded to an MQ endpoint for aggregation/data sharing. They may
also be saved locally for local monitoring/evaluation.

```yaml
PHAL:
  neon-phal-plugin-core-monitor:
    upload_enabled: False
    save_locally: True
```

## Messagebus API
Messagebus events are handled to collect various metrics. There is no defined 
set of supported metrics; any module may choose to report a metric to this plugin.

### Report Metric
Record an arbitrary metric by emitting:
```yaml
msg_type: neon.metric
data: 
  name: Metric name/type
  timestamp: Optional timestamp metric was collected (float epoch time)
  # Add any data that will be collected as part of this metric
```

### Get Metric
Get processed data for a collected metric.
```yaml
msg_type: neon.get_metric
data:
  name: Metric name/type (required)
```

### Get Raw Metric
Get raw data for collected metrics. This will return a list of dict data for the
requested metric (dict of metric name to list dict data if no metric requested).
```yaml
msg_type: neon.get_raw_metric
data:
  name: Metric name/type (or None to get all metrics)
```