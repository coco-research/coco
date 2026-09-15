---
name: email-security
description: Use for authorized email security review including phishing analysis, header authentication (SPF/DKIM/DMARC), BEC patterns, and mailbox token abuse research.
user-invocable: true
---

# Email Security & Phishing Analysis

## 适用场景

- 钓鱼邮件拆解与 IOC
- SPF/DKIM/DMARC 配置评估
- BEC 商务邮件欺诈模式
- OAuth 应用钓鱼 / 邮箱令牌滥用（联合 llm/cloud 身份）
- 安全意识演练设计（授权）

## 工作流

```text
□ 完整原始头：Received 链、From/Return-Path 一致性
□ SPF/DKIM/DMARC 对齐结果
□ URL 沙箱与附件静态（联合 malware-analysis）
□ 仿冒品牌与回复地址差异
□ 租户：反钓鱼策略、外部标记、MFA、OAuth app 同意
```

## 工具链

| 工具 | 用途 |
|------|------|
| 邮件客户端「查看源」 | 头 |
| dig/nslookup | SPF/DMARC 记录 |
| urlscan / 沙箱 | 链接与附件 |
| 租户管理中心 | 策略 |

## 参考

- `references/email-auth-checklist.md`
- `../malware-analysis/` `../attack-chain/`（钓鱼阶段） `../windows-ad/`（令牌）
