---
title: "项目6-Selenium 动态页面实战"
---

# 项目6：Selenium 动态页面实战

有些数据不是网页刚打开就存在，而是 JavaScript 点击或等待后才出现。Selenium 能操作真实浏览器。为了让第一次练习稳定、安全，本章先用本地动态页面，不登录任何网站，也不提交真实信息。

## 本章任务

打开本地页面，点击“加载资讯”，等待 JavaScript 生成三条内容，再把标题打印出来。

## 安装

```bash
pip install selenium
```

电脑安装并更新 Chrome 后，较新的 Selenium 通常会自动管理浏览器驱动。第一次启动可能稍慢。

![安装 Selenium 参考](Pasted%20image%2020260712153200.png)

## 第一步：保存本地动态页面

在同一文件夹新建 `dynamic_demo.html`，或下载本章的[演示页面](dynamic_demo.html)。

```html
<!doctype html>
<meta charset="utf-8">
<title>动态资讯演示</title>
<button id="load-button">加载资讯</button>
<ul id="news"></ul>
<script>
  document.querySelector("#load-button").onclick = function () {
    setTimeout(function () {
      document.querySelector("#news").innerHTML = `
        <li class="news-item">睡眠与健康</li>
        <li class="news-item">科学运动建议</li>
        <li class="news-item">合理膳食提示</li>`;
    }, 800);
  };
</script>
```

点击后不会立刻出现内容，800 毫秒后 JavaScript 才会把列表写进页面。这就是我们需要“等待”的原因。

## 第二步：用 Selenium 操作页面

保存为 `selenium_dynamic.py`，或下载本章的[完整代码](selenium_dynamic.py)。

```python
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def main():
    page = Path(__file__).with_name("dynamic_demo.html").as_uri()
    driver = webdriver.Chrome()

    try:
        driver.get(page)
        driver.find_element(By.ID, "load-button").click()

        wait = WebDriverWait(driver, 5)
        items = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".news-item"))
        )

        for item in items:
            print(item.text)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
```

代码顺序只有四步：打开页面、点击按钮、等待元素出现、读取文字。`finally` 中的 `quit()` 保证无论是否报错都关闭浏览器。

![浏览器运行参考](Pasted%20image%2020260712155544.png)

## 运行和检查

```bash
python selenium_dynamic.py
```

终端应该依次打印三条资讯标题，Chrome 会在程序结束后自动关闭。

## 常见问题

| 现象 | 处理 |
|---|---|
| `No module named selenium` | 执行 `pip install selenium` |
| 浏览器没有打开 | 确认 Chrome 已安装；再升级 Selenium：`pip install -U selenium` |
| 等待超时 | 确认两个文件在同一个文件夹；把等待时间从 `5` 改为 `10` |
| 想看浏览器不要自动关闭 | 学习时暂时注释 `driver.quit()`，完成后再恢复 |

## 小练习

1. 在 HTML 中增加一条 `<li class="news-item">` 内容。
2. 在 Python 中打印 `len(items)`，看看一共找到几条。
3. 把标题保存为 CSV 文件。

## 操作截图参考

![输出结果参考](Pasted%20image%2020260712165257.png)
