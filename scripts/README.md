# 脚本说明

## 1. 模块定位

`scripts/` 用于放置可重复执行的开发与维护脚本。脚本应尽量保持幂等，不得内嵌真实密钥或生产凭据。

## 2. 当前脚本

- `bootstrap_local_admin.py`
  - 用途：创建或确认本地测试管理员账号
  - 典型场景：登录后台、验证 `auth`、跑前端联调

## 3. 使用示例

```bash
cd /home/ecs-user/HiFleetAI
DATABASE_BACKEND=sqlite SQLITE_DB_PATH=data/app-dev.db DATABASE_URL= \
PATH="/home/ecs-user/HiFleetAI/.venv/bin:$PATH" \
python3 scripts/bootstrap_local_admin.py --username admin --display-name admin --password admin
```

## 4. 使用约束

- 该脚本只应用于本地测试环境
- 不要把真实用户账号初始化逻辑混入该脚本
- 不要把脚本输出的本地密钥或敏感信息写回仓库

## 5. 相关文档

- `docs/测试与部署维护指南.md`
- `docs/验证报告/当前系统验证报告.md`
