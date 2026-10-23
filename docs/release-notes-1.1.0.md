# FlashData Python SDK v1.1.0

[FlashData](https://flashdata.dev) · [API documentation](https://flashdata.dev/docs)

Choose JSON, plain text or Markdown responses with both `FlashData` and
`AsyncFlashData`. Existing calls keep their JSON dictionaries and defaults.

- Use `accept="text/plain"` for a string with the original response fields.
- Use `respond_with="markdown"` on realtime queries or `jobs.result()` for Markdown.
  JSON responses put it in `content`; text responses include metadata and Markdown.
- Background submissions, batches and job status also support `accept`.
- Type hints follow the selected format and reject incompatible background options.
- Result reads preserve job metadata, structured errors and credential separation.
  Reading an existing result in another format does not repeat the query.

Requires Python 3.10+. Install or upgrade:

```sh
python -m pip install --upgrade "flashdata==1.1.0"
```

The [GitHub release](https://github.com/flashdatadev/flashdata-python/releases/tag/v1.1.0)
also provides the wheel and source archive. For examples, see
[response formats](response-formats.md).

## 简体中文

1.1.0 为同步和异步客户端新增独立的 `accept` 与 `respond_with` 选项。
默认仍返回 JSON；纯文本返回字符串，Markdown 可位于 JSON 的 `content` 字段或纯文本响应中。
后台提交和任务状态支持 `accept`，Markdown 用于实时内容及已完成结果。需要 Python 3.10+。
