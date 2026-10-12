# iOS 侧回灌与导出通道（M1 证据）

> 日期：2026-10-12
> 设备：iPhone12,1，iOS 26.6.2（Windows 主机，Apple Mobile Device Service 运行中）
> 工具：pymobiledevice3 11.28.2（AFC）、exiftool 13.59、ffprobe 9.0.2

## 1. 通道对比（已验证）

| 通道 | 读取 | 写入 | 备注 |
| --- | --- | --- | --- |
| MTP（Windows WPD） | 可用但**视频残缺** | **不可用**（CopyHere 无效果） | 见 `ios-reference.md` |
| **AFC（pymobiledevice3）** | **可用且完整** | **可用** | 根目录为 `/var/mobile/Media`，可访问 `/DCIM` |

## 2. AFC 连接与目录（已验证）

```
$ pymobiledevice3 usbmux list
  ProductType: iPhone12,1   ProductVersion: 26.6.2

$ pymobiledevice3 afc ls /
/Airlock /Downloads /Books /Photos /Deferred /Music /DCIM /iTunes_Control
/MediaAnalysis /PhotoData /PublicStaging /AirFair

$ pymobiledevice3 afc ls /DCIM
/DCIM/100APPLE  /DCIM/101APPLE  /DCIM/102APPLE  /DCIM/.MISC
```

## 3. 导出完整 Live Photo（已验证）

```
$ pymobiledevice3 afc pull /DCIM/102APPLE/IMG_2002.MOV  <本地>   → 2,190,388 字节
$ pymobiledevice3 afc pull /DCIM/102APPLE/IMG_2002.HEIC <本地>   → 1,589,933 字节
```

`ffprobe` 可正常解析视频（hevc 1920x1440、pcm_s16le 音轨、另有 3 条附加轨），**文件完整**。

对比：MTP 导出的同名 MOV 为 4,818,853 字节且**缺少 moov**，不可用。结论：**iOS 侧取原始文件必须走 AFC，不能走 MTP**。

## 4. 配对机制：图片与视频共用同一个 UUID（已验证）

静态图（Apple MakerNote）：

```
[Apple] ContentIdentifier : 1CA7450A-CC0A-42F6-BF45-396BBBD95AD2
[Apple] LivePhotoVideoIndex : 575676416
[Apple] PhotoIdentifier : E59AAEE2-EDA7-451F-B71C-7AFEEB741B04
```

视频（`mdta` 域，位于 moov/meta 中）：

```
com.apple.quicktime.content.identifier              = 1CA7450A-CC0A-42F6-BF45-396BBBD95AD2
com.apple.quicktime.still-image-time                （存在，值待解析）
com.apple.quicktime.live-photo-still-image-transform（存在）
com.apple.quicktime.live-photo-still-image-transform-reference-dimensions（存在）
com.apple.quicktime.live-photo.vitality-score / -scoring-version（存在）
com.apple.quicktime.location.ISO6709                （存在）
```

**两侧 ContentIdentifier 完全一致** → iOS 的配对依据是：图片 MakerNote 中的 `ContentIdentifier` 与视频 mdta 中 `com.apple.quicktime.content.identifier` 取同一个 UUID（标准 UUID 字符串格式）。

附加轨的 metadata handler 为 `Core Media Metadata`，格式 `mebx`（与鸿蒙视频的附加轨格式相同）。

## 5. 回灌写入：可写入，但相册未索引（已验证）

```
$ pymobiledevice3 afc push <本地 IMG_9001.JPG> /DCIM/102APPLE/IMG_9001.JPG   → 无报错
$ pymobiledevice3 afc ls /DCIM/102APPLE
/DCIM/102APPLE/IMG_9001.JPG   ← 已存在
```

回读校验（排除"写入损坏"）：

| 项 | 值 |
| --- | --- |
| 回读文件 SHA256 | `4C13269B744078E8D9DD3B028DBB4BC02DDA3B65A86BD42374B9962AD472086E` |
| 本地源文件 SHA256 | 同上（一致） |
| 文件大小 | 3,656,845 |
| ffprobe | `format_name=image2`（有效 JPEG） |

设备侧结果：**「照片」应用中未出现该图片**（用户在设备上确认）。

结论（已验证部分）：AFC 具备 DCIM 写入权限且内容正确，但**写入不等于被相册索引**。

推测（待验证）：现代 iOS 的相簿由照片库数据库管理，外部写入 DCIM 的文件不会自动入库；是否可通过重启触发 `assetd` 扫描导入，需实测确认。

> 说明：`afc` 无 mkdir 子命令，写入需使用已存在目录（如 `102APPLE`）。

## 6. 本机可用通道盘点（已验证）

| 通道 | 本机状态 |
| --- | --- |
| iTunes | 未安装 |
| iCloud for Windows（照片上传目录） | 未安装 / 未启用 |
| Apple 官方 UWP 应用（Apple Devices 等） | 无 |
| Apple Mobile Device Service（驱动） | 运行中 |
| AFC（pymobiledevice3） | 可用（读、写均可） |

## 7. 候选回灌方案（待评估）

| 方案 | 可行性 | 成本 | Live Photo 保留 | 可脚本化 |
| --- | --- | --- | --- | --- |
| A'. 写入 DCIM 后重启设备触发索引 | 待验证 | 极低 | 未知 | 是 |
| B. iCloud for Windows 上传目录 | 官方，需安装并登录 | 中 | 待验证 | 是（复制文件） |
| C. iTunes / Apple Devices 照片同步 | 官方，需安装 | 中 | 待验证（可能转码） | 有限 |
| D. 第三方工具（iMazing 等） | 待评估 | 中 | 待验证 | 取决于是否提供 CLI |
| E. 自建 iOS App（PhotoKit 配对资源写入） | 官方 API，原理上可行 | 高（需开发者签名，按 N1.7 评审） | 是 | 是 |
| F. iPhone 端快捷指令 + iCloud Drive | 待验证 | 低 | 可能丢失配对 | 半自动 |
