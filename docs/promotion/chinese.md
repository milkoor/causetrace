# 中文推广 — 定向技术分享

**策略：** 不在中文社区做大范围推广。中文技术社区目前缺乏 coding agent 重度用户，过早推广会产生需求错配。

**唯一值得做的：** 在知乎发一篇技术分析，标题不出现 causetrace，而是讨论 coding agent 的可观测性问题。

---

## 知乎文章方向

**标题：** Claude Code 跑了一百多步，出问题了怎么查？

**内容结构：**
1. 场景描述：一个长 session 之后 agent 做了意料之外的修改
2. 问题：翻日志全是扁平的 "Read/Write/Bash"，看不出因果关系
3. 分析：为什么"时间线"不适合 coding agent 的调试
4. 解决思路：记录 parent_event_id，构建因果链
5. 展示对比：同一个 session 的时间线 vs 因果树
6. 开源工具 causetrace（末尾一笔带过，不占主体）

**核心主张：** 不是推广工具，是分享一个发现——coding agent 的运行时不适合用日志抽象，因果图是更好的原语。

**文章末尾可复现入口：**

```bash
pip install "causetrace @ git+https://github.com/milkoor/causetrace.git@v0.2.5"
causetrace demo
```
