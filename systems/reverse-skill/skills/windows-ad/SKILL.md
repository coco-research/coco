---
name: windows-ad
description: Use for authorized Active Directory and Windows identity attacks including Kerberos, AD CS, BloodHound paths, NTLM relay, and domain privilege escalation research.
user-invocable: true
---

# Windows / Active Directory Security

## 适用场景

- 域渗透、Kerberoasting、AS-REP、委派
- AD CS（ESC1–ESC8 等）证书攻击
- BloodHound / SharpHound 攻击路径
- NTLM Relay / Coercer 强制认证
- 本地提权到域路径（Potato 等作为跳板）

## 与 attack-chain 关系

- **多阶段从外网到域控** → PRIMARY 可仍是 `attack-chain/`，本 skill 为 **AD 专科**
- **已在域内专注身份** → PRIMARY = 本 skill

## 工作流

### 1. 枚举

```bash
# 示例 Impacket / 内置（需凭据与授权）
nxc smb <range> -u user -p pass
bloodhound-python -d domain.local -u user -p pass -c All -ns <DC>
```

### 2. 常见路径（先图后枪）

```text
□ Kerberoast / AS-REP → 离线破解
□ ACL 滥用（GenericAll/WriteDacl）
□ 委派（非约束/约束/基于资源）
□ AD CS 模板错误 → Certipy
□ 中继：LLMNR/NBT-NS + ntlmrelayx（确认授权）
```

### 3. 凭证与横向

```text
□ secretsdump / lsassy / mimikatz（严格授权与清理）
□ PtH / PtT / 黄金票仅在授权红队范围
□ 每步写 Evidence；高危等用户确认
```

## 工具链

| 工具 | 用途 |
|------|------|
| BloodHound / SharpHound | 路径图 |
| Certipy | AD CS |
| Impacket / NetExec | 横向与枚举 |
| Rubeus / Mimikatz | 票据与凭证（授权） |
| Coercer / Responder | 强制认证 / 投毒 |

## 参考

- `references/ad-attack-paths.md`
- `../pentest-tools/references/network-attack-defense.md`
- `../attack-chain/`
