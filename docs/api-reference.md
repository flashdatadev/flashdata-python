# API reference

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

`FlashData` and `AsyncFlashData` expose the same resource names. Public responses are
JSON dictionaries by default, typed by `flashdata.types`. The API preserves wire names such
as `createdAt` and `availableCredits`. Source helpers return a source response in realtime
mode and `AsyncSubmission` in background mode. Each accepts a per-request `timeout`.
`accept="text/plain"` returns a string. Realtime queries and `jobs.result()` also
accept `respond_with="markdown"`, returning `MarkdownQueryResult` for JSON. See
[response formats](response-formats.md) for supported methods and examples.

| Source | Python helper | Main input |
| --- | --- | --- |
| `google_search` | `google.search` | query |
| `google_images` | `google.images` | query |
| `google_news` | `google.news` | query |
| `google_shopping` | `google.shopping` | query |
| `google_videos` | `google.videos` | query |
| `google_places` | `google.places` | query |
| `youtube_search` | `youtube.search` | query |
| `youtube_search_extended` | `youtube.search_extended` | query |
| `youtube_metadata` | `youtube.metadata` | video_id |
| `youtube_transcript` | `youtube.transcript` | video_id |
| `youtube_captions` | `youtube.captions` | video_id |
| `youtube_trainability` | `youtube.license_check` | video_id |
| `youtube_channel` | `youtube.channel` | handle |
| `youtube_suggestions` | `youtube.suggestions` | query |
| `youtube_download` | `youtube.download` | video_id (background only) |

See [source guides](sources/index.md) for parameter names, constraints and response fields.
Full endpoint schemas are in the repository's `openapi.json`; it describes supported
developer APIs rather than browser session or administrative operations.

## Clients

```{autoclass} flashdata.FlashData
:members: close
```

```{autoclass} flashdata.AsyncFlashData
:members: aclose
```

## Resource methods

Async counterparts use the same signatures and return shapes, with `await` for requests
and `async for` for iterators. Polling `timeout` is a waiting deadline; other `timeout`
arguments override HTTP operation timeouts.

```{autoclass} flashdata._resources.Queries
:members:
:undoc-members:
```

```{autoclass} flashdata._resources.Jobs
:members:
:undoc-members:
```

```{autoclass} flashdata._resources.Bulk
:members:
:undoc-members:
```

```{autoclass} flashdata._resources.Account
:members:
:undoc-members:
```

```{autoclass} flashdata._resources.Public
:members:
:undoc-members:
```

## Exceptions

```{automodule} flashdata.errors
:members:
:show-inheritance:
```
