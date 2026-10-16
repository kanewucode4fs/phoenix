此目录包含一组资源清单和覆盖配置，用于定义不同的 Kubernetes 部署方案。
可从仓库根目录执行这些部署。

示例：

```shell
kubectl apply -k kustomize/base
```

上述命令会创建一个包含 PostgreSQL 的 Phoenix 单节点部署。
