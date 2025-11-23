# 微博爬虫使用指南

## 1. 环境准备

确保已安装 Python 3.8+。

在终端中运行以下命令安装依赖：

```bash
pip install -r requirements.txt
playwright install chromium
```

## 2. 登录 (首次运行)

运行登录脚本：

```bash
python login.py
```

1. 浏览器会自动打开微博登录页。
2. 请在浏览器中**手动扫码登录**。
3. 登录成功并跳转到首页后，脚本会自动保存 `state.json` 文件并退出。

## 3. 配置与抓取

打开 `scraper.py` 文件，修改顶部的配置区域：

```python
TARGET_USER_ID = "1669879400"  # 目标用户的 ID (从用户主页 URL 获取)
START_DATE = "2023-01-01"      # 开始日期
END_DATE = "2023-12-31"        # 结束日期
```

然后运行爬虫：

```bash
python scraper.py
```

## 4. 结果

抓取的数据将以 Markdown 文件形式保存在 `output` 文件夹中，文件名格式为 `YYYY-MM-DD.md`（按天归档）。

## 注意事项

- **频率限制**: 脚本中包含简单的延时，但如果抓取量巨大，建议增加延时或分批抓取。
- **选择器失效**: 微博网页结构经常更新。如果发现抓取不到内容，可能需要更新 `scraper.py` 中的 CSS 选择器（如 `article`, `detail_text` 等）。
