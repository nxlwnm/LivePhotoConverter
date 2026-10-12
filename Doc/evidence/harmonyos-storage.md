# 鸿蒙侧动态照片存储与获取（M1 证据）

> 日期：2026-10-12
> 设备：HUAWEI Pura 80 Pro+（USB 调试已授权，MTP 与 hdc 均可用）
> 工具：hdc 3.2.0f、exiftool 13.59、ffprobe 9.0.2
> 样本：一组动态照片（`IMG_20261012_165648.heic` + `IMG_20261012_165648.mp4`）

## 1. 存储形态：双文件（已验证）

设备上「图库 / 相机」目录中，动态照片表现为**同名的一对文件**：

```
IMG_20261012_165648.heic    静态图
IMG_20261012_165648.mp4     动态视频
```

- 纯照片只有 `.heic`；纯视频为 `VID_<时间戳>.mp4`；动态照片为 `IMG_` 前缀的 heic + mp4 成对出现。
- **显示名 ≠ 媒体库存储名**：媒体库内部存储为 `IMG_1791795508_5549.heic`，显示名为 `IMG_20261012_165648.heic`。

## 2. 静态图是否内嵌视频：否（已验证）

对 `IMG_20261012_165648.heic` 检查：

- `exiftool` 未发现 MPF / Trailer / 内嵌视频相关字段；关键词扫描（Motion / Live / Moving / MicroVideo / MPImage / Embedded）无命中；
- `ffprobe` 只识别到 HEIF 的图像项（主图与缩略图），无视频轨；
- 文件大小 1,230,823 字节，与一张普通 12MP HEIC 相称，不含额外视频负载。

结论：**HEIC 是纯静态图，视频以独立文件存在**。

## 3. 配对机制：不在文件内（已验证，机制待进一步确认）

- 两个文件中均未发现苹果式的关联标识（Content Identifier）类字段；
- 也未发现华为自定义的动态照片关联字段；
- 目前可依赖的配对依据：**显示名（不含扩展名）相同**。

> 待验证：媒体库内部是否另有记录（URI 关联），以及该记录是否可通过 mediatool 等途径读取。

## 4. 获取通道（已验证）

### 4.1 hdc shell 受限于权限

```
$ hdc shell id
uid=2000(shell) ... context=u:r:sh:s0
$ hdc shell ls /
ls: /: Permission denied
$ hdc smode
[Fail]Cannot set root run mode in undebuggable version.
```

→ 无法直接访问文件系统，必须走媒体库工具或 MTP。

### 4.2 mediatool（媒体库命令行工具）

```
$ hdc shell mediatool query IMG_20261012_165648.heic -u
find 1 result
uri
"file://media/Photo/6251/IMG_1791795508_5549/IMG_20261012_165648.heic"

$ hdc shell mediatool recv "file://media/Photo/6251/..." /data/local/tmp/lpcv
Table Name: Photos
/data/local/tmp/lpcv/IMG_20261012_165648.heic

$ hdc file recv /data/local/tmp/lpcv/IMG_20261012_165648.heic <本地>
FileTransfer finish, Size:1230823
```

限制：

- `mediatool ls -l <dir>` 对各类目录均返回 `path invalid`（该子命令用法待确认）；
- `mediatool query` 只命中 **Photos 表**，查询同名 `.mp4` 返回 `find 0 result` → **当前无法通过 mediatool 取到视频**。

### 4.3 MTP（Windows Shell COM）

设备以 WPD 方式挂载（`Get-PnpDevice` 可见 `HUAWEI Pura 80 Pro+`，Class=WPD），可用 Shell.Application 枚举与复制：

```
内部存储 / 图库 / 相机 → IMG_20261012_165648.heic (1,230,823)
                          IMG_20261012_165648.mp4 (5,942,310)
```

MTP 可同时取到静态图与视频，是**目前唯一能拿全一对文件的通道**。

### 4.4 原始性交叉验证（已验证）

| 通道 | 文件大小 | SHA256（前 16 位） |
| --- | --- | --- |
| mediatool recv + hdc file recv | 1,230,823 | `85A7B31B0D134E5E` |
| MTP 复制 | 1,230,823 | `85A7B31B0D134E5E` |

两条通道文件**完全一致**，说明取到的是原始件，未被二次转码或剥离。

## 5. 静态图规格（已验证）

| 项 | 值 |
| --- | --- |
| 格式 | HEIC（HEIF，HEVC still image） |
| 分辨率 | 3072x4096（IFD0 记为 4096x3072，方向标记待核对） |
| 色彩/动态范围 | BT.2020 + HLG，MaxCLL 900，MaxPicAverage 203 → **HDR** |
| ImageDescription | `_cuva` |
| Make / Model | HUAWEI / HUAWEI Pura 80 Pro+ |
| 拍摄参数 | 1/100s, F2.2, ISO 640, 24mm 等效 |

## 6. 视频规格（已验证）

| 项 | 值 |
| --- | --- |
| 容器 / 编码 | MP4 / HEVC（CUVA HDR Video） |
| 分辨率 | 1920x1440，Rotation 90（实际竖屏 1440x1920） |
| 帧率 | 60 fps |
| 时长 | 2.38 s |
| 码率 | 19.9 Mbps |
| 音频 | AAC，单声道，32 kHz，48 kbps |
| Encoder | Openharmony6.1 |
| 附加轨 | NRT Metadata（mebx，timed_metadata，2.3 MB） |

> 附加轨内容待确认（M2）：非文本，可能是 HDR 动态元数据或深度数据，每 0.03s 一个样本。

## 7. 对方案的影响

- 视频时长 2.38s、HEVC、1920x1440 与 iOS Live Photo 的常见约束接近，转码压力小；
- **HDR 为 CUVA 标准**（图像与视频均标记 CUVA），与 iOS 侧的 HDR 方案不同，HDR 能否保留存在实质风险（对应 R13）；
- 配对不在文件内，转换时以「同名文件对」作为配对依据；
- 取视频需依赖 MTP 通道（mediatool 暂不支持），Device Bridge 的实现应把 MTP 作为鸿蒙侧主通道，mediatool 作为静态图补充通道。
