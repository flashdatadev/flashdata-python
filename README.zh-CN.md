# FlashData Python SDK

[English](https://github.com/flashdatadev/flashdata-python/blob/main/README.md) | [简体中文](https://github.com/flashdatadev/flashdata-python/blob/main/README.zh-CN.md)

[FlashData](https://flashdata.dev) · [API 文档](https://flashdata.dev/docs)

为 Python 应用、研究数据管道、搜索监控和检索流程提供 Google 搜索结果与 YouTube 数据。

获取网页、新闻、购物、图片、视频和本地搜索结果；发现 YouTube 视频，读取元数据和已有字幕轨道；
提交后台任务，或通过视频 ID 文件批量处理数据。SDK 提供同步与异步客户端、类型定义、
本地参数校验和结构化错误。需要 Python 3.10 或更高版本。

## FlashData 是什么？

[FlashData](https://flashdata.dev) 提供 Google 搜索数据、YouTube 数据和云端媒体交付 API，
面向开发者与数据团队，适用于搜索监控、研究、数据分析、内容发现以及 AI 应用的检索流程。

你可以获取多种 Google 搜索结果，发现 YouTube 视频，读取视频元数据、已有字幕、频道数据和许可标签。
根据工作量选择实时请求、后台任务、混合批次或视频 ID 文件批量处理。
媒体下载会将音频或视频直接交付到你自己的云存储。
详情见 [API 文档](https://flashdata.dev/docs)和[价格说明](https://flashdata.dev/pricing)。

## 按使用场景选择工作流

| 想要构建的功能 | 从这里开始 |
| --- | --- |
| 为 AI 助手提供网页上下文和来源链接 | [Google 搜索](#搜索-google) |
| 行业研究或新闻监控 | [新闻搜索](#跟踪行业新闻) |
| 按主题发现视频或学习资源 | [YouTube 搜索](#按主题查找-youtube-视频) |
| 视频分析和内容目录补全 | [视频元数据](#获取视频元数据) |
| 为视频摘要、搜索或检索获取文本 | [已有字幕文本](#为-ai-工作流获取字幕文本) |
| 根据一组视频 ID 构建数据集 | [批量元数据导出](#构建-youtube-元数据数据集) |
| 将音频或视频交付到自己的云存储桶 | [批量媒体下载](#批量下载-youtube-视频) |
| 继续中断的批量任务 | [恢复任务](#恢复已启动的批量任务) |

以下示例负责获取数据；摘要、检索索引、调度和 AI 模型调用由应用实现。

## 安装

```sh
pip install flashdata
```

纯文本与 Markdown 响应选项需要 1.1.0 或更新版本。开发时可使用[源码安装](#从源码安装)。

## 配置 API 密钥

从你的 [FlashData 账户](https://flashdata.dev)获取 API 密钥，并通过客户端的 `api_key` 参数显式传入。
以下示例用 `os.getenv("FLASHDATA_API_KEY")` 读取环境变量；也可以传入密钥管理服务提供的值。
SDK 不会自动加载 `.env` 文件，如需使用，请先由应用加载配置。

```sh
# macOS / Linux
export FLASHDATA_API_KEY="YOUR_API_KEY"
```

```powershell
# PowerShell
$env:FLASHDATA_API_KEY = "YOUR_API_KEY"
```

下面的代码块都是独立示例。完成安装并设置 API 密钥后，将任一代码块保存为 `quickstart.py`，然后运行：

```sh
python quickstart.py
```

## 搜索 Google

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.google.search("coffee roasters", gl="us", hl="en", num=5)
    for page in response["results"]:
        for hit in page.get("organic", []):
            print(hit["title"], hit["link"])
```

默认响应是普通字典。外层 `response["results"]` 包含各数据源的结果对象；
Google 网页搜索条目位于其中的 `organic` 列表中。其他数据源使用各自的字段结构。
本次请求消耗的积分（Credits）位于 `response["usage"]["credits"]`。

## 选择响应格式

需要 `flashdata` 1.1.0 或更新版本。

默认返回 JSON 字典。设置 `accept="text/plain"` 返回字符串；
设置 `respond_with="markdown"` 选择 Markdown 内容。同步与异步客户端均支持这些选项。

| `accept` | `respond_with` | 返回值 |
| --- | --- | --- |
| `"application/json"`（默认） | 省略 | 包含原始 `results` 的字典 |
| `"text/plain"` | 省略 | 原始字段的文本形式 |
| `"application/json"`（默认） | `"markdown"` | Markdown 位于 `content` 字段的字典 |
| `"text/plain"` | `"markdown"` | 元数据及 Markdown 内容 |

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.google.search("vector databases", respond_with="markdown")
    print(response["content"])
    text = client.youtube.transcript(
        "dQw4w9WgXcQ", accept="text/plain", respond_with="markdown"
    )
    print(text)
```

后台提交、批量提交及 `jobs.get()` 也支持 `accept`。
后台任务的 Markdown 内容请通过 `jobs.result(job_id, respond_with="markdown")` 获取。
更换已完成结果的格式不会重新查询或消耗查询积分。
详见[响应格式指南](docs/response-formats.md)。

## 跟踪行业新闻

收集行业新闻的标题、发布来源和文章链接，供研究工具或监控脚本使用。

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.google.news("battery recycling", gl="us", hl="en", num=5)
    for payload in response["results"]:
        for article in payload.get("news", []):
            print(article.get("title"), article.get("source"), article.get("link"))
```

## 按主题查找 YouTube 视频

发现相关视频，并获取可用于后续元数据或字幕请求的视频 ID。

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.search("python tutorial", max_results=5)
    for payload in response["results"]:
        for video in payload.get("results", []):
            print(video.get("videoId"), video.get("title"), video.get("channel"))
```

## 获取视频元数据

补全视频目录中的标题、频道、时长和播放量。请将示例 ID 替换为你要处理的视频 ID。

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.metadata("dQw4w9WgXcQ", include_formats=False)
    for video in response["results"]:
        print(video.get("title"), video.get("channel"))
        print("Seconds:", video.get("duration"), "Views:", video.get("viewCount"))
```

## 为 AI 工作流获取字幕文本

读取已有的英文自动字幕文本，供应用生成摘要或建立检索索引。
API 返回文本；摘要生成或向量化由你的应用完成。

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.transcript("dQw4w9WgXcQ", language="en", auto=True)
    for track in response["results"]:
        print(track.get("fullText", ""))
```

字幕取决于视频已有的语言轨道；不会自动转写或翻译缺失的字幕。
如需人工上传的字幕，可使用下面的 `captions` 示例。

## 读取 YouTube 字幕轨道

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    response = client.youtube.captions("dQw4w9WgXcQ", language="en", auto=False)
    for track in response["results"]:
        print(track["languageCode"], track["isAutoGenerated"])
        for segment in track.get("segments", [])[:3]:
            print(segment["start"], segment["text"])
```

`captions` 默认选择上传的字幕轨道（`auto=False`），`transcript` 默认选择自动生成的轨道（`auto=True`）。
请指定视频实际拥有的语言和轨道。轨道不存在时，API 会返回错误；服务不会生成或翻译字幕。

## 使用 asyncio

```python
import os
import asyncio
from flashdata import AsyncFlashData

async def main():
    async with AsyncFlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
        response = await client.youtube.search("python tutorial", max_results=5)
        for payload in response["results"]:
            for video in payload.get("results", []):
                print(video["title"], video["videoId"])

asyncio.run(main())
```

`AsyncFlashData` 提供相同的资源接口。请求使用 `await`，分页和批量结果迭代器使用 `async for`。
请在应用或事件循环内复用客户端。

## 提交后台任务

```python
import os
from flashdata import FlashData

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    submitted = client.youtube.metadata("dQw4w9WgXcQ", mode="async", include_formats=False)
    job_id = submitted["id"]
    print("Save this job ID:", job_id, flush=True)
    client.jobs.wait(job_id, timeout=300, poll_interval=2)
    result = client.jobs.result(job_id)
    print(result)
```

等待前请保存任务 ID，以便进程重启后继续读取同一任务。
`wait()` 返回已完成的任务记录，`result()` 获取 JSON 结果。
不同查询可使用[混合批次](docs/jobs.md)；每行一个 YouTube 视频 ID 的 UTF-8 文件可使用[批量任务](docs/bulk.md)。

## 构建 YouTube 元数据数据集

创建 `video-ids.txt`，每行填写一个 YouTube 视频 ID：

```text
dQw4w9WgXcQ
jNQXAC9IVRw
```

以下示例完成创建任务 → 上传 ID → 启动 → 等待 → 导出 NDJSON（每行一个 JSON 对象）。
每行包含一个输入条目的处理状态和数据。

```python
import json
import os
from pathlib import Path
from flashdata import FlashData

with (
    FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client,
    Path("videos.ndjson").open("x", encoding="utf-8") as output,
    Path("videos.ndjson.job.json").open("x", encoding="utf-8") as record,
):
    receipt = client.bulk.create({
        "source": "youtube_metadata",
        "options": {"include_formats": False},
    })
    bulk_id = receipt["job"]["id"]
    print("Save this bulk ID:", bulk_id, flush=True)
    json.dump({"id": bulk_id}, record)
    record.flush()
    os.fsync(record.fileno())
    client.bulk.upload_file(receipt, Path("video-ids.txt"))
    client.bulk.start(bulk_id)
    completed = client.bulk.wait(bulk_id, timeout=3600, poll_interval=5)

    for row in client.bulk.rows(bulk_id):
        output.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("Saved videos.ndjson; counts:", completed["counts"])
    if completed["counts"].get("failed") or completed["counts"].get("invalid"):
        raise RuntimeError("Some items failed; inspect the saved rows before retrying")
```

内联程序会在上传前将已受理的任务 ID 保存到 `videos.ndjson.job.json`。进程重启或超时后，使用下方的
[恢复流程](#恢复已启动的批量任务)，不要重新运行创建代码。示例导出使用独占创建模式，拒绝覆盖已有文件。

如需开箱即用的脚本，在仓库根目录运行以下命令。它会在上传前自动将任务记录保存到
`OUTPUT.job.json`，并保留逐项失败的导出结果：

```sh
python examples/bulk.py video-ids.txt --output artifacts/videos.ndjson
python examples/bulk.py --bulk-id bulk_YOUR_SAVED_ID --output artifacts/videos-recovered.ndjson
```

创建与恢复命令是两种不同的运行方式；仅在需要恢复时运行第二条命令，并替换任务 ID。
其他批量来源包括 `youtube_transcript`、`youtube_captions` 和 `youtube_trainability`；
每个任务共用一套选项。参数说明见[批量指南](docs/bulk.md)。

## 批量下载 YouTube 视频

创建 `video-ids.txt`，每行一个 11 位视频 ID：

```text
dQw4w9WgXcQ
jNQXAC9IVRw
```

创建私有配置文件 `private-storage.json`，填写目标云存储信息。下面以 S3 为例：

```json
{
  "storage_type": "s3",
  "storage_url": "your-media-bucket",
  "region": "us-east-1",
  "object_prefix": "youtube",
  "access_key": "YOUR_ACCESS_KEY",
  "secret_key": "YOUR_SECRET_KEY"
}
```

请用真实凭证替换占位符，并将配置文件保存在版本控制之外。
然后创建批量下载任务、上传 ID 文件、启动处理并读取每个视频的状态：

```python
import json
import os
from pathlib import Path
from flashdata import FlashData

storage = json.loads(Path("private-storage.json").read_text(encoding="utf-8"))

with (
    FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client,
    Path("downloads.ndjson").open("x", encoding="utf-8") as output,
    Path("downloads.ndjson.job.json").open("x", encoding="utf-8") as record,
):
    receipt = client.bulk.create({
        "source": "youtube_download",
        "options": {
            "download_type": "audio_video",
            "video_quality": "<=720",
            "output_format": "mp4",
            "storage": storage,
        },
    })
    bulk_id = receipt["job"]["id"]
    print("Save this bulk ID:", bulk_id, flush=True)
    json.dump({"id": bulk_id}, record)
    record.flush()
    os.fsync(record.fileno())
    client.bulk.upload_file(receipt, Path("video-ids.txt"))
    client.bulk.start(bulk_id)

    completed = client.bulk.wait(bulk_id, timeout=3600, poll_interval=5)
    print("Counts:", completed["counts"])
    for row in client.bulk.rows(bulk_id):
        output.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(row["video_id"], row["status"])
    if completed["counts"].get("failed") or completed["counts"].get("invalid"):
        raise RuntimeError("Some items failed; inspect downloads.ndjson before retrying")
```

以上程序会在上传前将已受理的 ID 保存到 `downloads.ndjson.job.json`，
将交付回执保存到 `downloads.ndjson`，并拒绝覆盖已有文件。
逐项失败时会先保存回执，再报告错误。

媒体文件交付到你配置的存储桶。`bulk.rows()` 读取任务的 JSON 结果记录，
包括每个视频的状态，以及 `results` 中的数据源输出；它不会把媒体文件下载到本机。
请检查最终计数和每行状态：任务整体完成时，仍可能存在失败条目。
下载按照实际交付的字节数计费，云存储服务商可能另外收费。

进程重启或轮询超时后，可用保存的 ID 调用 `client.bulk.get()`、`client.bulk.wait()` 和 `client.bulk.rows()`，
继续读取已有任务。详见[批量控制与恢复](docs/bulk.md)、[下载选项](docs/sources/youtube_download.md)
和[支持的存储服务商](docs/storage.md)。

可运行示例会在 NDJSON 导出文件旁保存任务记录，并支持继续读取已启动的任务，不会重复提交：

```sh
python examples/bulk_download.py video-ids.txt --storage-file private-storage.json --output artifacts/downloads.ndjson
python examples/bulk_download.py --bulk-id bulk_YOUR_SAVED_ID --output artifacts/downloads-recovered.ndjson
```

第二条命令仅用于恢复已启动的任务，请替换保存的任务 ID，并使用新输出路径保留之前的导出结果。

尚处于 `awaiting_upload` 的草稿仍需上传文件并调用 `start`；暂停的任务需解决暂停原因后调用 `resume`。

### 改为交付 MP3 音频

相同 ID 文件和存储配置也可用于音频任务。将上述内联请求的下载选项改为
`download_type="audio"` 和 `output_format="mp3"`，并移除 `video_quality`；或者在仓库根目录运行：

```sh
python examples/bulk_download.py video-ids.txt --audio --storage-file private-storage.json --output artifacts/audio.ndjson
```

## 恢复已启动的批量任务

将 `bulk_YOUR_SAVED_ID` 替换为元数据或下载任务先前打印并保存的 ID。
此流程只等待和读取已有任务，不创建任务、不重新上传 ID，也不会重新提交下载。

```python
import json
import os
from pathlib import Path
from flashdata import FlashData

bulk_id = "bulk_YOUR_SAVED_ID"
with FlashData(api_key=os.getenv("FLASHDATA_API_KEY")) as client:
    completed = client.bulk.wait(bulk_id, timeout=3600, poll_interval=5)
    with Path("recovered.ndjson").open("x", encoding="utf-8") as output:
        for row in client.bulk.rows(bulk_id):
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("Saved recovered.ndjson; counts:", completed["counts"])
    if completed["counts"].get("failed") or completed["counts"].get("invalid"):
        raise RuntimeError("Some items failed; inspect the saved rows before retrying")
```

等待超时只会停止本地轮询，已受理的服务端任务仍会继续。`awaiting_upload` 状态仍需
原始上传描述和显式 `start`；已暂停任务需先修复原因，再调用 `resume`。示例任务记录不含签名上传描述，
不能仅凭 ID 恢复上传前中断的进程。不要将存储凭据或签名 URL 写到普通任务记录中。

请及时导出结果，内部结果在完成后保留 24 小时。详情见[批量控制与恢复](docs/bulk.md)。

## 处理错误

```python
import os
from flashdata import APIError, FlashData, SubmissionUnknownError

with FlashData(api_key=os.getenv("FLASHDATA_API_KEY"), timeout=120) as client:
    try:
        response = client.google.search("coffee", timeout=60)
    except APIError as error:
        print(error.status_code, error.code, error.request_id, error.retry_after)
    except SubmissionUnknownError:
        # 服务端可能已接受本次付费请求；再次提交前请先核实状态。
        raise
```

SDK 每个请求只发送一次，不会自动重试付费查询或修改操作。
关于限流、轮询超时、任务失败和存储错误，请参阅[错误与恢复](docs/errors.md)。
[客户端配置](docs/client.md)介绍超时、代理和 TLS。Python 的超时与轮询间隔以秒为单位。

## 支持的 API

| 资源 | 方法 |
| --- | --- |
| Google | `search`、`images`、`news`、`shopping`、`videos`、`places`，以及限制页数的 `pages` |
| YouTube | `search`、`search_extended`、`metadata`、`transcript`、`captions`、`license_check`、`channel`、`suggestions`、`download` |
| Queries | `realtime`、`submit`、`batch`，接收具有类型定义的 API 请求字典 |
| Jobs | `get`、`wait`、`result` |
| Bulk | `create`、`upload_file`、`start`、`get`、`list`、`iter_jobs`、`update`、`pause`、`resume`、`cancel`、`wait`、`manifest`、`part`、`iter_rows`、`rows` |
| Account | `access`、`balance`、`pricing`、`limits`、`usage` |
| Public | `sources`、`plans`、`health`、`status`，无需密钥 |

全部 15 个数据源支持后台提交和混合批次，其中 14 个数据源也支持实时请求。
媒体下载在后台执行，需要配置自己的云存储。批量任务支持元数据、转录、字幕、许可标签和下载。
许可标签不代表获得了媒体复用或模型训练授权。

## 指南与可运行示例

以下详细指南目前以英文提供：

- [快速入门](docs/getting-started.md)：安装、鉴权和响应结构。
- [数据源指南](docs/sources/index.md)：每个数据源的参数与使用方式。
- [示例目录](examples/README.md)：命令行输入、易读输出和 JSON/CSV/NDJSON 导出。
- [分页](docs/pagination.md)、[后台任务与批次](docs/jobs.md)、[批量数据集](docs/bulk.md)。
- [云存储](docs/storage.md)、[账户与用量](docs/account.md)、[API 参考](docs/api-reference.md)。

```sh
python examples/google_search.py "coffee roasters" --output artifacts/search.json
python examples/search_to_csv.py "coffee roasters" --max-pages 2 --output artifacts/search.csv
python examples/youtube_captions.py dQw4w9WgXcQ --language en
python examples/async_query.py "python tutorial" --output artifacts/result.json
```

这些命令调用真实 API 并消耗积分。运行 `python examples/offline.py` 可在无需账户、无需网络的情况下体验模拟请求。
[SDK 对照说明](docs/sdk-parity.md)列出了 Python、TypeScript/JavaScript、Go 和 CLI 的 API 覆盖、语言差异、工作流行为和验证范围。

批量脚本会在任何 API 调用之前拒绝覆盖已有导出或 `OUTPUT.job.json` 记录。
超时或中断后，请使用已保存的 ID 和新输出路径恢复；不要重新执行创建。
保留的空记录表示需先核实提交结果，再决定是否创建新任务。

## 从源码安装

在本仓库的源码目录中执行：

```sh
python -m pip install .
```

## 开发

```sh
python -m pip install -e ".[dev,docs]"
python -m pytest
python -m ruff check src tests examples scripts docs/conf.py
python -m ruff format --check src tests examples scripts docs/conf.py
python -m mypy src/flashdata
python -m sphinx -n -W --keep-going -b html docs docs/_build/html
python -m build
python scripts/verify_package.py
```

默认测试使用模拟传输和本地 HTTP 服务。真实 API 测试需要显式启用，详见[贡献指南](CONTRIBUTING.md)。
项目采用 MIT 许可证。敏感安全问题请按照[安全政策](SECURITY.md)私下报告。
