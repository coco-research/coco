---
name: protocol-reverse
description: Use for authorized reverse engineering of custom binary protocols, Protobuf/gRPC, WebSocket frames, and PCAP-driven protocol recovery.
user-invocable: true
---

# Protocol Reverse Engineering

## 适用场景

- 自定义 TCP/UDP 二进制协议
- Protobuf / gRPC / FlatBuffers / MessagePack
- WebSocket / MQTT / 私有 RPC
- PCAP / PCAPNG 还原字段与状态机
- 客户端-服务端校验、序列号、加密帧头

## 不走本 skill

| 情况 | 去哪 |
|------|------|
| 仅 HTTP 参数签名 / JS 加密 | `js-reverse/` |
| 仅 TLS 证书问题 | `pentest-tools/` 或浏览器代理 |
| 固件内协议栈深挖 + 仿真 | `firmware-pentest/` 后再回本 skill |

## 工作流

### Phase 1 — 采集与分诊

```text
□ 拿到样本：PCAP / 代理导出 / 客户端日志 / 二进制
□ 标记方向：C→S / S→C；是否有握手、心跳、重连
□ 固定头？魔数？长度字段？TLV？定长？
□ 是否压缩（zlib/gzip/lz4）或加密（AES/ChaCha 帧内）
□ tshark -r cap.pcap -T fields -e frame.number -e ip.src -e tcp.payload
```

### Phase 2 — 帧布局还原

```text
□ 对齐多个同类消息，找不变字节 / 自增序列号
□ 长度字段：大端/小端、含头/不含头
□ 校验：CRC16/32、checksum、HMAC 位置
□ 画出状态机：Connect → Auth → Ready → Request/Response → Close
□ 工具：Wireshark 自定义 dissector 草稿 / ImHex / 010 Editor 模板 / Kaitai Struct
```

### Phase 3 — 序列化与加密

```text
□ Protobuf：.proto 恢复（blackboxprotobuf / pbtk / protoc --decode_raw）
□ gRPC：HTTP/2 headers + protobuf body
□ 加密：找密钥派生（客户端 so/dll/JS）→ 联合 ida-reverse / js-reverse / apk-reverse
□ 重放：仅在授权 scope 内；先无害字段再敏感操作
```

### Phase 4 — 产物

```text
MUST 产出：
- 消息类型表（name / opcode / fields）
- 至少 1 条可复现的解码命令或脚本
- Evidence：原始 hex 摘录 + 解码结果（脱敏）
```

## 工具链

| 工具 | 必需 | 用途 |
|------|------|------|
| tshark / Wireshark | 强烈建议 | PCAP 解析 |
| Python3 | 是 | 解码脚本 |
| blackboxprotobuf | 可选 | 未知 protobuf |
| ImHex / 010 | 可选 | 结构模板 |
| IDA / r2 / Ghidra | 按需 | 客户端序列化函数，见对应 skill |

## 参考

- `references/protocol-workflow.md` — 帧布局与 Protobuf 速查
- 相关：`../ida-reverse/` `../js-reverse/` `../firmware-pentest/` `../pentest-tools/`
