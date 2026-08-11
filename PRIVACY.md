# 盯亿帧（Key Face Frame）隐私政策

更新日期：2026 年 8 月 12 日

盯亿帧是一款在 Mac 本机筛选视频人物关键帧的工具。1.0 不要求注册账号，也不会把用户的视频或抽取的画面发送给开发者。

## 本机处理的数据

- 用户通过系统文件选择器主动选择的视频，仅用于本机抽帧和 Core ML 分析。
- 生成的关键帧预览、导出图片、剪辑标记和 ComfyUI 素材包，仅保存在用户选择的位置。
- 本地历史摘要，包括视频名称、授权书签、处理时间、关键帧索引和处理统计，保存在用户 Mac 的 Application Support 目录。
- 用户主动导出的诊断包只包含 App 版本、处理参数、文件名称和历史摘要，不包含原视频或关键帧图像，也不会自动上传。

## 开发者不收集的数据

- 不上传或收集原视频、抽样帧、关键帧和素材包。
- 不使用第三方广告、跨 App 追踪或自建行为分析 SDK。
- 不读取用户未选择的本地文件。
- 不自动发送诊断信息或用户反馈。

## 购买与反馈

永久解锁由 Apple StoreKit 处理。开发者只读取 Apple 返回的本机权益状态；付款资料、退款和购买历史由 Apple 按其政策处理。用户如主动通过支持渠道反馈，开发者只使用用户主动提供的信息处理该次请求。

## 用户控制

用户可以删除导出的文件，并可通过删除 App 的 Application Support 数据清除本地历史。删除历史不会删除用户的原视频。

## 联系方式

- 支持邮箱：425452267@qq.com
- 支持网址：https://github.com/MarcelLeon/key-face-frame/issues

---

# Key Face Frame Privacy Policy

Last updated: August 12, 2026

Key Face Frame is an on-device macOS utility for finding people-focused keyframes in video. Version 1.0 requires no account and does not send imported videos or extracted frames to the developer.

## Data processed on the Mac

- Videos explicitly selected through the system file picker are used only for on-device frame extraction and Core ML analysis.
- Keyframe previews, exported images, editing markers, and ComfyUI material packages remain in locations selected by the user.
- Local history summaries, including video names, security-scoped bookmarks, processing times, keyframe indexes, and processing statistics, are stored in the app's Application Support directory.
- User-initiated diagnostic packages contain only the app version, processing settings, file names, and history summaries. They exclude original videos and keyframe images and are never uploaded automatically.

## Data the developer does not collect

- Original videos, sampled frames, keyframes, and material packages are not uploaded or collected.
- The app contains no third-party advertising, cross-app tracking, or custom analytics SDK.
- The app does not read files the user has not selected.
- Diagnostics and feedback are not sent automatically.

## Purchases and feedback

The lifetime unlock is processed by Apple StoreKit. The app reads only the entitlement state returned by Apple. Payment details, refunds, and purchase history are handled by Apple under Apple's policies. If a user voluntarily contacts support, the developer uses only the information supplied by the user to respond to that request.

## User controls

Users can delete exported files and clear local history by removing the app's Application Support data. Clearing history does not delete original videos.

## Contact

- Support email: 425452267@qq.com
- Support URL: https://github.com/MarcelLeon/key-face-frame/issues
