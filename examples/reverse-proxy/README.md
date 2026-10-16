<a id="deploying-phoenix-with-a-reverse-proxy"></a>

# 使用反向代理部署 Phoenix

本示例介绍如何通过反向代理部署 Phoenix，并为应用设置自定义根路径。示例使用 [`traefik`](https://doc.traefik.io/traefik/)，也可以使用 Nginx 等其他反向代理服务器实现相同效果。

<a id="steps"></a>

## 操作步骤

查看 `traefik` 配置文件 [traefik.toml](./traefik.toml) 和 [routes.toml](./routes.toml)。这些文件配置了一个监听 `9999` 端口的反向代理，应用根路径为 `/phoenix_root_path`，并将流量转发到本地默认端口上运行的 Phoenix 实例。

下载并解压适合当前平台的 [`traefik` 二进制文件](https://github.com/traefik/traefik/releases)，将其放在当前目录，然后启动代理：

```
./traefik --configFile=traefik.toml
```

接着安装 Phoenix：

```
pip install arize-phoenix
```

设置 `PHOENIX_HOST_ROOT_PATH` 环境变量，使其与上述配置文件中的根路径一致。

```
export PHOENIX_HOST_ROOT_PATH="/phoenix_root_path"
```

运行 Phoenix：

```
python -m phoenix.server.main serve
```

现在应该可以通过 `traefik` 代理，在 http://127.0.0.1:9999/phoenix_root_path 访问 Phoenix 界面。


<a id="references"></a>

## 参考资料

本指南改编自介绍相同部署方式的 [FastAPI 指南](https://fastapi.tiangolo.com/advanced/behind-a-proxy/#testing-locally-with-traefik)。
