# Executable examples

Run commands from the repository root after installation/build. Source examples perform
one paid query, except the offline and account examples. Download reads a private file
named by `FLASHDATA_STORAGE_FILE`. No example creates an account or purchases Credits.

| Example | Purpose |
| --- | --- |
| offline | Simulated Google result; no key or network |
| account | Free access, balance, pricing and limits reads |
| async_query | Background submission, ID persistence, explicit wait, result retrieval |
| batch | Mixed-source batch, preserving per-item results |
| pagination | At most two paid Google pages, stopping on empty results |
| bulk | Create, upload and start a metadata collection; prints ID without waiting |
| async_client | Python's native async client (Python repository only) |

- `google_search.py`: [guide](../docs/sources/google_search.md).
- `google_images.py`: [guide](../docs/sources/google_images.md).
- `google_news.py`: [guide](../docs/sources/google_news.md).
- `google_shopping.py`: [guide](../docs/sources/google_shopping.md).
- `google_videos.py`: [guide](../docs/sources/google_videos.md).
- `google_places.py`: [guide](../docs/sources/google_places.md).
- `youtube_search.py`: [guide](../docs/sources/youtube_search.md).
- `youtube_search_extended.py`: [guide](../docs/sources/youtube_search_extended.md).
- `youtube_metadata.py`: [guide](../docs/sources/youtube_metadata.md).
- `youtube_transcript.py`: [guide](../docs/sources/youtube_transcript.md).
- `youtube_captions.py`: [guide](../docs/sources/youtube_captions.md).
- `youtube_trainability.py`: [guide](../docs/sources/youtube_trainability.md).
- `youtube_channel.py`: [guide](../docs/sources/youtube_channel.md).
- `youtube_suggestions.py`: [guide](../docs/sources/youtube_suggestions.md).
- `youtube_download.py`: [guide](../docs/sources/youtube_download.md).

The tests execute all source examples against fake transports. Local fixture data is
illustrative; it does not prove upstream availability. To run source examples live,
provide your own key and run the chosen script explicitly.
