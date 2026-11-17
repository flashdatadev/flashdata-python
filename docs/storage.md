# Cloud storage and downloads

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

YouTube Download delivers media into a destination you configure. Pass it in
`params.storage` for individual/batch queries or `options.storage` for bulk downloads.
Bulk data output can use `options.result_storage`. Files are not returned as local media
attachments. The SDK's signed result reader retrieves a JSON result/manifest.

| storage_type | Required credential/configuration fields in addition to storage_url |
| --- | --- |
| s3 | access_key, secret_key; region when required by your bucket |
| s3_compatible | access_key, secret_key, public HTTPS endpoint_url |
| oss | access_key, secret_key, region's public HTTPS endpoint_url |
| cos | access_key, secret_key, ap-* region; bucket includes APPID |
| bos | access_key, secret_key, region bj/su/hkg |
| tos | access_key, secret_key, supported region |
| gcs | service_account object with project_id, client_email, private_key |
| azure | account_name and container SAS sas_token with write permission |

`storage_url` is a bucket name (Azure: container), not a full object URL. `object_prefix`
is optional. Keep credentials in your private file/secret manager and do not commit it.
See [the current storage examples](https://flashdata.dev/docs/sources/youtube_download)
for provider restrictions and supported regions. The server validates the complete
provider-specific destination and media option combination.

Example private S3 configuration; replace placeholders in a protected file:

```json
{"storage_type":"s3","storage_url":"your-media-bucket","region":"us-east-1","access_key":"YOUR_ACCESS_KEY","secret_key":"YOUR_SECRET_KEY"}
```

## Temporary STS credentials

S3, S3-compatible providers that issue temporary credentials, OSS, COS, BOS and TOS
accept an optional `session_token` with its matching temporary `access_key` and
`secret_key`. AWS/BOS/TOS call it SessionToken, OSS calls it SecurityToken, and COS
calls it Token (paired with TmpSecretId/TmpSecretKey). Azure continues to use
`sas_token`; GCS uses `service_account`.

```python
from flashdata import FlashData

storage = {
    "storage_type": "s3",
    "storage_url": "your-media-bucket",
    "region": "us-east-1",
    "access_key": "YOUR_TEMPORARY_ACCESS_KEY",
    "secret_key": "YOUR_TEMPORARY_SECRET_KEY",
    "session_token": "YOUR_SESSION_TOKEN",
}
with FlashData(api_key="your-api-key") as client:
    receipt = client.youtube.download("dQw4w9WgXcQ", storage=storage)
    print(receipt["id"])
```

Use the same object in `options.storage` for bulk downloads or
`options.result_storage` for bulk data exports. Omit `session_token` for long-term
credentials. Temporary credentials must remain valid through queueing, processing,
uploads and retries; FlashData does not refresh them automatically.

For a paused bulk data job whose input scan has finished, renew the result-storage
credentials with `client.bulk.update(bulk_id, {"options": {"result_storage": {
"access_key": "NEW_TEMPORARY_ACCESS_KEY", "secret_key": "NEW_TEMPORARY_SECRET_KEY",
"session_token": "NEW_SESSION_TOKEN"}}})`, then resume the job. The destination
stays unchanged. Do not save credential values in job checkpoints.

Download supports audio/video/audio-only selection, video quality constraints, frame-rate
constraints, source audio language, audio quality, format selection, a yt-dlp format
selector, metadata sidecars and start/end timestamps. All parameters are documented in
[the download source guide](sources/youtube_download.md). Storage credentials go to
FlashData for delivery, and cloud permissions, access and retention remain yours.

Transcripts/captions read existing selected tracks; FlashData does not generate a missing
transcript or translate it. The license-label endpoint reports a Creative Commons label;
it does not grant media reuse or model-training permission.
