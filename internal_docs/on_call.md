<a id="on-call-guide"></a>
# 值班指南

作为 Phoenix 和 Openinference 的维护者，你需要对项目的健康状况负责，包括及时回应 issue、拉取请求和提问。这项责任较重，因此我们采用轮流值班，避免任何一个人负担过重。值班安排通过 PagerDuty 管理，轮到你值班时会收到通知。

<a id="responsibilities"></a>
## 职责

- 尽可能准确地回答问题，最好附上文档链接、临时解决方法或 GitHub issue
  - slack
    - \#phoenix-support
  - github
    - Phoenix
      - [问题](https://github.com/Arize-ai/phoenix/issues)
      - [讨论](https://github.com/Arize-ai/phoenix/discussions)
    - Openinference
      - [问题](https://github.com/Arize-ai/openinference/issues)
- 复现、确认并分诊各开源仓库中的缺陷报告
  - Phoenix
    - [尚无评论的新 issue](https://github.com/search?q=repo%3AArize-ai%2Fphoenix+-author%3Acephalization+-author%3Aaxiomofjoy+-author%3Arogerhyang+-author%3Amikeldking+-author%3Aanticorrelator+-author%3Ajgilhuly+state%3Aopen+comments%3A0&type=issues&ref=advsearch&s=created&o=desc)
  - Openinference
    - [尚无评论的新 issue](https://github.com/search?q=repo%3AArize-ai%2Fopeninference+-author%3Acephalization+-author%3Aaxiomofjoy+-author%3Arogerhyang+-author%3Amikeldking+-author%3Aanticorrelator+-author%3Ajgilhuly+state%3Aopen+comments%3A0&type=issues&ref=advsearch&s=created&o=desc)
- 接受或拒绝拉取请求，对可接受的请求进行评审：[Phoenix](https://github.com/Arize-ai/phoenix/pulls) - [Openinference](https://github.com/Arize-ai/openinference/pulls)

<a id="priority-levels-for-bug-fix"></a>
### 缺陷修复优先级

- P0：应尽快修复，暂停其他任务。
- P1：应在一周内修复。
- P2：应在下一个迭代内修复。虽然有临时解决方法，但缺陷影响明显。
- P3：待办事项。

<a id="tips"></a>
## 建议

- 在 GitHub 上通过 Watch 订阅 phoenix 和 openinference 的全部活动，以接收包括讨论在内的所有通知。
- 尽量及时回应问题和反馈，即使只是感谢对方报告问题。
- 练习搭建带有 Openinference 插桩配置的简单 Python 和 TypeScript 脚本。
  - 制作可快速复制和调整的模板，便于复现或确认缺陷。
  - 尝试使用 uv 简化 Python 依赖管理。
