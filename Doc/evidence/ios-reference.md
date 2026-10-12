# iOS 侧 Live Photo 参照样本与通道探查（M1 证据）

> 日期：2026-10-12
> 设备：Apple iPhone（Windows 上 WPD 可见：Apple Mobile Device Service 运行中）
> 工具：exiftool 13.59、ffprobe 9.0.2、Windows Shell COM（MTP）
> 样本：iPhone 通过 MTP 导出的一对文件 `IMG_2002.JPG` / `IMG_2002.MOV`

## 1. 静态图侧的关联标识（已验证）

```
[Apple]  MakerNoteVersion   : 16
[Apple]  ContentIdentifier  : 5A16463F-FABA-4A8A-A626-A710DE9ABE69
[Apple]  LivePhotoVideoIndex: 575676416
[Apple]  PhotoIdentifier    : E59AAEE2-EDA7-451F-B71C-7AFEEB741B04
```

关键结论：

- **ContentIdentifier 是标准 UUID 字符串**（不是此前推测的 17 字节随机值）；
- 另有两个字段：`LivePhotoVideoIndex`、`PhotoIdentifier`；
- 这些字段位于 **Apple MakerNote** 中，写入时需要 exiftool 或等价工具支持 Apple MakerNote 写入（可行性待 M2 验证）。

> 待验证：视频侧对应字段（Content Identifier / 静止帧时刻）的名称与位置——当前样本的视频文件不可用，见下节。

## 2. MTP 导出的视频不可用（已验证）

`IMG_2002.MOV`（4,818,853 字节）结构检查：

| atom | 是否存在 |
| --- | --- |
| ftyp | 有（offset 4） |
| wide | 有（offset 24） |
| mdat | 有（offset 32） |
| **moov** | **缺失** |

- `ffprobe`：`moov atom not found`，无法解析；
- `exiftool`：在偏移 0x49070d 处提示 trailer 数据异常；
- 两次导出文件大小完全一致，排除"复制未完成"因素。

结论：通过 MTP 从 iPhone 导出的 Live Photo 视频**缺少 moov，无法使用**。需要换方式获取完整视频（如 iCloud Drive / 文件应用导出）。

## 3. MTP 写入 iPhone 被拒（已验证）

向 iPhone 的 `202610_a` 目录执行 `CopyHere` 写入测试：

```
BEFORE: IMG_2002.MOV, IMG_2002.JPG
AFTER : IMG_2002.MOV, IMG_2002.JPG   （无新增）
```

结论：**iPhone 的 WPD 视图为只读**，MTP 不能用于回灌。鸿蒙侧可用的 MTP 复制思路在 iOS 侧不成立。

## 4. 对方案的影响

- iOS 回灌**不能走 MTP**，必须另寻通道；
- 静态图侧配对字段已明确（UUID 形式的 ContentIdentifier），是后续构造的关键依据；
- 视频侧元数据仍需一份**完整**的 iOS Live Photo 视频才能确认。
