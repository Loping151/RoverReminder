# RoverReminder

![icon](./ICON.png)

## 部署方式

```shell
├── gsuid_core
│   ├── gsuid_core
│   │   ├── plugins
│   │   │   ├── XutheringWavesUID
│   │   │   ├── RoverReminder


cd gsuid_core/gsuid_core/plugins
git clone --depth=1 https://github.com/Loping151/RoverReminder
```

依赖：XutheringWavesUID 及其数据表

## 邮件配置

只需要修改两个文件：

1) 配置文件路径：`gsuid_core/data/RoverReminder/mail/config.json`

启动后会自动生成，直接修改该文件即可。

2) 邮件模板路径：`gsuid_core/data/RoverReminder/mail/template.html`

启动后会自动生成，直接修改该文件即可。

模板内可用变量：
- `{{uid}}`
- `{{user_id}}`
- `{{bot_id}}`
- `{{bot_self_id}}`
- `{{stamina}}`
- `{{threshold}}`
- `{{time}}`
- `{{stamina_image}}`（base64 图片，可为空）

自定义模板（可选）：
- 修改 `gsuid_core/gsuid_core/plugins/RoverReminder/RoverReminder/mail/custom_template.py`
- 自定义时会优先使用该文件内的 `build_stamina_html` 函数

QQ 邮箱说明：
- 需在 QQ 邮箱后台开启 SMTP 服务并获取授权码
- 配置中的 `auth_code` 为授权码，非登录密码
- SMTP 服务器：`smtp.qq.com`，端口常用 `465`(SSL) 或 `587`(STARTTLS) ，加密必需启用

## 使用说明

- 开启推送：`ww开启体力推送`
- 关闭推送：`ww关闭体力推送`
- 设置邮箱：`ww推送邮箱 123456789@gmail.com`
- 设置阈值：`ww推送阈值 180`
