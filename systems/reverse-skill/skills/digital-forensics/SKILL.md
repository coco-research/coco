---
name: digital-forensics
description: Use for authorized digital forensics including memory dumps, disk timelines, PCAP investigation, artifact triage, and IR evidence preservation.
user-invocable: true
---

# Digital Forensics & IR Artifacts

## 适用场景

- 内存转储分析（Volatility 2/3）
- 磁盘/ E01 / 落地文件时间线
- PCAP 溯源与协议还原（可联合 `protocol-reverse/`）
- 主机伪影：Prefetch、Shimcache、Event Log、浏览器历史
- 应急响应 IOC 提炼（联合 `malware-analysis/` / `threat-hunting/`）

## 工作流

### 1. 保全

```text
□ 计算 SHA256；记录时区与采集命令
□ 工作在副本上；原始只读
□ chain of custody 备注写入 timeline
```

### 2. 内存

```bash
vol -f mem.dmp windows.info
vol -f mem.dmp windows.pslist
vol -f mem.dmp windows.netscan
vol -f mem.dmp windows.cmdline
```

### 3. 主机伪影

```text
□ 事件日志：Security / PowerShell / Sysmon
□ 持久化：Run 键、服务、计划任务、WMI
□ 执行痕迹：Amcache、Prefetch、BAM
```

### 4. 网络

```text
□ tshark 统计会话与 DNS
□ 导出可疑流 → protocol-reverse 或 malware C2 分析
```

## 工具链

| 工具 | 用途 |
|------|------|
| Volatility 3 | 内存 |
| Timeline Explorer / Plaso | 超级时间线 |
| tshark | PCAP |
| Eric Zimmerman 工具集 | Windows 伪影 |
| Autopsy / FTK Imager | 磁盘 |

## 参考

- `references/forensics-triage.md`
- `../malware-analysis/` `../threat-hunting/` `../protocol-reverse/`
