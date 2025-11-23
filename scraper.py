import os
import time
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
from utils import parse_weibo_time

# --- 配置区域 ---
TARGET_USER_ID = "1645215240"  # 替换为目标用户的 ID (例如: 1669879400)
START_DATE = "2025-11-1"      # 抓取开始日期 (包含)
END_DATE = "2025-11-18"        # 抓取结束日期 (包含)
OUTPUT_DIR = "output"
STATE_FILE = "state.json"
# ----------------

def scrape_weibo():
    if not os.path.exists(STATE_FILE):
        print(f"错误: 未找到 {STATE_FILE}。请先运行 login.py 进行登录。")
        return

    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    data_list = []
    processed_ids = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # 设为 False 以便观察
        context = browser.new_context(storage_state=STATE_FILE)
        page = context.new_page()

        url = f"https://weibo.com/u/{TARGET_USER_ID}"
        print(f"正在访问: {url}")
        page.goto(url)
        # page.wait_for_load_state("networkidle") # 微博动态请求多，networkidle 容易超时
        try:
            page.wait_for_load_state("domcontentloaded", timeout=60000)
        except Exception:
            print("页面加载超时，尝试继续...")

        # 初始等待，让页面加载
        time.sleep(3)

        no_new_data_count = 0
        consecutive_old_count = 0
        
        while True:
            # 0. 检查是否被重定向到了热搜页
            if "hot/weibo" in page.url:
                print("警告: 检测到跳转至热搜页，尝试重新导航回用户主页...")
                page.goto(url)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(3)
                continue

            # 获取当前所有微博卡片
            # 注意：微博的类名可能会变，这里尝试用较通用的属性选择器
            # 常见的微博卡片容器通常包含 action-type="feed_list_item" 或者特定的 class
            # 目前微博Web版(weibo.com)结构较复杂，通常是 article 标签或者 div class="vue-recycle-scroller__item-view"
            # 我们尝试查找包含具体内容的容器
            
            # 策略：获取所有可能是微博内容的元素
            # 观察发现微博正文通常在 class 包含 "detail_text" 的 div 中
            cards = page.locator("article").all() # 尝试获取 article 标签，新版微博常用
            
            if not cards:
                # 备选选择器
                cards = page.locator("div[class*='Feed_body_']").all()

            print(f"当前页面检测到 {len(cards)} 条微博卡片...")
            
            new_items_found = False

            for card in cards:
                try:
                    # 获取微博文本内容用于去重（或者尝试获取 mid）
                    # 这里的去重逻辑可能需要优化，最好能找到 mid
                    # 暂时用文本前20个字符 + 时间 作为指纹
                    
                    # 1. 解析时间 (为了生成ID，还是需要先解析时间，或者先尝试从链接获取ID)
                    # 时间通常在 header 的链接里，或者 class 包含 'time'
                    time_element = card.locator("a[class*='head-info_time']").first
                    if not time_element.is_visible():
                         # 尝试另一种时间选择器
                         time_element = card.locator("a[href*='/status/']").first
                    
                    if not time_element.is_visible():
                        continue

                    # 2. 生成唯一ID (简单去重)
                    # 尝试获取微博链接中的 mid
                    post_link = time_element.get_attribute("href")
                    # 如果没有链接，暂时无法生成可靠ID，只能先解析时间
                    
                    time_str = time_element.inner_text()
                    post_time = parse_weibo_time(time_str)
                    
                    if not post_time:
                        continue

                    post_id = post_link.split("/")[-1].split("?")[0] if post_link else str(post_time)
                    
                    # --- 关键修改: 先检查是否已处理 ---
                    if post_id in processed_ids:
                        continue
                    # --------------------------------

                    # 3. 时间过滤逻辑
                    if post_time > end_dt:
                        # 比结束时间还晚（太新了），跳过
                        # 但这说明我们还在数据流中，重置无数据计数器
                        no_new_data_count = 0 
                        continue
                    
                    if post_time < start_dt:
                        # 比开始时间还早（太旧了）
                        # 注意：可能是置顶微博，不能立即停止
                        consecutive_old_count += 1
                        print(f"发现旧微博 ({post_time})，连续旧微博计数: {consecutive_old_count}")
                        
                        if consecutive_old_count >= 5:
                            print(f"连续发现 {consecutive_old_count} 条过往微博，停止抓取。")
                            save_data(data_list)
                            return
                        # 即使是旧微博，如果是置顶的，我们可能已经处理过了（上面的 check 会拦住）
                        # 如果是第一次见到的旧微博（比如刚滚动出来的），我们跳过它，但计数器加1
                        
                        # --- 关键修复: 如果ID已经处理过，不要增加计数器 ---
                        # 虽然上面的 check (line 104) 已经过滤了 processed_ids，
                        # 但为了双重保险，以及防止逻辑漏洞，这里再次确认。
                        # 实际上，代码运行到这里说明 post_id 不在 processed_ids 中。
                        # 但是，如果页面发生跳转导致重新加载了旧数据，我们需要确保这些旧数据不会导致立即停止。
                        # 现在的逻辑是：只要是新的旧数据，就计数。
                        # 问题在于：如果滚动导致页面刷新，可能会看到之前没见过的旧数据（因为动态加载）。
                        # 我们增加一个判断：只有当 consecutive_old_count 连续增加时才停止。
                        # 另外，为了防止误判，我们可以增加计数器的阈值，或者检查是否真的到底了。
                        
                        continue
                    
                    # 如果时间符合要求（或者太新），重置计数器
                    consecutive_old_count = 0
                    
                    processed_ids.add(post_id)
                    new_items_found = True

                    # 4. 处理“展开全文”
                    # 查找“展开”按钮。通常是 "展开" 文本
                    expand_btn = card.locator("text='展开'").first
                    if expand_btn.is_visible():
                        print(f"点击展开全文: {post_id}")
                        # 显式滚动到可见区域
                        # expand_btn.scroll_into_view_if_needed()
                        # time.sleep(0.5)
                        
                        # 使用 JS 直接点击，绕过 Playwright 的可见性检查
                        try:
                            expand_btn.evaluate("el => el.click()")
                        except Exception as click_err:
                            print(f"JS点击失败，尝试常规点击: {click_err}")
                            try:
                                expand_btn.click(force=True, timeout=2000)
                            except:
                                pass
                                
                        # 等待一下文本展开
                        page.wait_for_timeout(1000)

                    # 5. 提取正文
                    # 正文通常在 class*='detail_text'
                    content_el = card.locator("div[class*='detail_text']").first
                    content = content_el.inner_text() if content_el.is_visible() else ""

                    # 6. 提取统计数据 (转发/评论/点赞)
                    # 底部工具栏
                    footer = card.locator("footer").first
                    stats_text = footer.inner_text() if footer.is_visible() else ""
                    
                    print(f"抓取到: {post_time} - {content[:20]}...")

                    data_list.append({
                        "id": post_id,
                        "time": post_time,
                        "content": content,
                        "link": f"https://weibo.com{post_link}" if post_link and not post_link.startswith("http") else post_link,
                        "stats_raw": stats_text
                    })

                except Exception as e:
                    print(f"解析单条微博出错: {e}")
                    continue

            # 滚动页面
            # 逻辑修正：只要页面上有卡片，且我们在滚动，就不应该轻易判定为“无新数据”而停止
            # 只有当：
            # 1. 页面完全没有卡片 (len(cards) == 0)
            # 2. 或者连续多次滚动后，页面内容完全没变（可以通过检查页面高度或最后一个元素ID来实现，这里简化处理）
            
            # 如果本轮找到了新元素(new_items_found)，或者我们跳过了一些“太新”的元素(说明还在往下滚)，都算作有进展
            # 我们需要一个标志位来表示“是否还在有效滚动”
            
            # 在上面的循环中，如果我们因为 post_time > end_dt 而 continue，说明我们还在“太新”的区域，这是正常的
            # 只有当我们遍历了所有卡片，既没有新的（processed_ids），也没有“太新”的，才可能是到底了
            
            # 简化策略：只要 cards 数量 > 0，且我们没有触发“连续旧微博”停止，就继续滚
            # 但是为了防止真的到底了还在死循环，我们需要判断页面高度是否变化，或者是否真的没有新 ID 出现
            
            if new_items_found:
                no_new_data_count = 0
            else:
                # 如果没找到新 ID，可能是因为所有 ID 都处理过了，或者所有 ID 都太新了
                # 我们可以检查一下是否所有卡片都是“太新”的？
                # 简单点：如果连续 10 次滚动都没有新 ID 入库，再停止
                no_new_data_count += 1
            
            if no_new_data_count > 10: # 放宽限制到 10 次
                print("连续多次未发现新数据，可能已到底部或被限制。")
                break

            print("向下滚动...")
            # 模拟更像真人的滚动：分段滚动
            # 减慢速度：每次滚动距离减小，间隔增加
            for _ in range(5): # 增加分段次数
                page.mouse.wheel(0, 500) # 每次只滚 500 像素
                time.sleep(0.8 + (time.time() % 0.5)) # 间隔 0.8~1.3秒
            
            # 滚完一段后，多停一会儿，等待加载
            time.sleep(3)
            
            # page.evaluate("window.scrollTo(0, document.body.scrollHeight)") # 太快会导致跳转热搜
            
            # 检查是否到底部 (可选)
            
    save_data(data_list)

def save_data(data):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print(f"共抓取 {len(data)} 条微博。")
    
    # 按日期分组
    posts_by_date = {}
    for post in data:
        date_str = post['time'].strftime('%Y-%m-%d')
        if date_str not in posts_by_date:
            posts_by_date[date_str] = []
        posts_by_date[date_str].append(post)
    
    for date_str, posts in posts_by_date.items():
        file_name = f"{date_str}.md"
        file_path = os.path.join(OUTPUT_DIR, file_name)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {date_str} 微博存档\n\n")
                
                # 按时间正序排列 (从早到晚)
                posts.sort(key=lambda x: x['time'])
                
                for post in posts:
                    time_display = post['time'].strftime('%H:%M:%S')
                    f.write(f"## {time_display}\n\n")
                    f.write(f"**互动数据:** {post['stats_raw']}\n\n")
                    f.write(f"{post['content']}\n\n")
                    f.write(f"---\n\n")
                    
            print(f"已保存: {file_name} ({len(posts)} 条)")
        except Exception as e:
            print(f"保存文件 {file_name} 失败: {e}")
            
    print(f"所有数据已按日期归档至 {OUTPUT_DIR} 目录")

if __name__ == "__main__":
    scrape_weibo()
