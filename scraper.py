import requests
from bs4 import BeautifulSoup
import time
import random
import sqlite3
import re
import os
from urllib.parse import urljoin
import logging

# הגדרת לוגינג
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class AIxploriaScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.base_url = "https://www.aixploria.com"
        self.scraped_tools = []
        self.failed_urls = []
        self.processed_urls = set()
        
        # עמודים לגרידה
        self.main_pages = [
            "/en/ultimate-list-ai/",
            "/en/free-ai/", 
            "/en/top-100-ai/",
            "/en/last-ai/",
            "/en/category/ai-supertools/",
            "/en/category/amazing/",
            "/en/category/websites-ai/",
            "/en/category/image-generation/",
            "/en/category/video-generation/",
            "/en/category/text-generation/",
            "/en/category/code-generation/",
            "/en/category/ai-agents/",
            "/en/category/business/"
        ]
        
        self.init_database()
    
    def init_database(self):
        """יצירת מסד נתונים"""
        self.conn = sqlite3.connect('ai_tools_full.db')
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT UNIQUE,
                description TEXT,
                category TEXT,
                popularity TEXT,
                pricing TEXT,
                tags TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON ai_tools(name)')
        self.conn.commit()
        logger.info("✅ מסד נתונים נוצר")
    
    def delay(self):
        """עיכוב קצר"""
        time.sleep(random.uniform(0.5, 1.5))
    
    def get_page(self, url):
        """שליפת עמוד"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            self.delay()
            return response.text
        except Exception as e:
            logger.error(f"שגיאה בשליפת {url}: {e}")
            self.failed_urls.append(url)
            return None
    
    def find_tool_links(self, html_content):
        """חיפוש קישורי כלים"""
        soup = BeautifulSoup(html_content, 'html.parser')
        tool_links = []
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
                
            # המרה לURL מלא
            if href.startswith('/'):
                href = urljoin(self.base_url, href)
            
            # בדיקות בסיסיות
            if not href.startswith('https://www.aixploria.com/en/'):
                continue
                
            # דלג על עמודים שאינם כלים
            skip_patterns = [
                '/add-ai/', '/news/', '/blog/', '/about/', '/contact/',
                '/privacy/', '/terms/', '/sitemap/', '/login/', '/register/'
            ]
            
            if any(pattern in href for pattern in skip_patterns):
                continue
            
            # דלג על עמודי קטגוריות ראשיים
            if href.endswith('/category/') or href.endswith('/tag/'):
                continue
                
            # הוסף לרשימת כלים
            tool_links.append(href)
        
        return list(set(tool_links))  # הסר כפולים
    
    def extract_tool_data(self, html_content, url):
        """חילוץ נתוני כלי"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            # שם הכלי
            title = soup.find('h1') or soup.find('title')
            if not title:
                return None
                
            name = title.get_text().strip()
            name = re.sub(r'\s*\|\s*.*$', '', name)  # נקה מטקסט אחרי |
            name = name[:100].strip()
            
            if not name:
                return None
            
            # תיאור
            description = ""
            
            # חפש בכמה מקומות
            desc_areas = [
                soup.select('div.entry-content p'),
                soup.select('div.description p'),
                soup.select('main p'),
                soup.select('article p')
            ]
            
            for area in desc_areas:
                for p in area:
                    text = p.get_text().strip()
                    if text and len(text) > 30:
                        description += text + " "
                        if len(description) > 200:
                            break
                if len(description) > 200:
                    break
            
            # נקה תיאור
            description = re.sub(r'\s+', ' ', description.strip())
            description = description[:800]
            
            # **תנאי איכות - לא לשנות!**
            if len(description) < 100:
                logger.debug(f"🚫 תיאור קצר: {name} ({len(description)} תווים)")
                return None
            
            # פופולריות
            popularity = ""
            pop_match = re.search(r'\(\+(\d+)\)', str(soup))
            if pop_match:
                popularity = f"+{pop_match.group(1)}"
            
            # קטגוריה
            category = ""
            cat_link = soup.find('a', href=re.compile(r'/category/'))
            if cat_link:
                category = cat_link.get_text().strip()
            
            # מחיר
            pricing = ""
            text_lower = str(soup).lower()
            if 'free' in text_lower and 'trial' not in text_lower:
                pricing = "free"
            elif 'freemium' in text_lower or 'free trial' in text_lower:
                pricing = "freemium"
            elif 'paid' in text_lower or 'subscription' in text_lower:
                pricing = "paid"
            
            # תגיות
            tags = []
            tag_links = soup.find_all('a', href=re.compile(r'/tag/'))
            for tag_link in tag_links[:5]:  # מקסימום 5
                tag = tag_link.get_text().strip()
                if tag:
                    tags.append(tag)
            
            tool_data = {
                'name': name,
                'url': url,
                'description': description,
                'category': category,
                'popularity': popularity,
                'pricing': pricing,
                'tags': ', '.join(tags)
            }
            
            logger.info(f"✅ כלי נמצא: {name} ({len(description)} תווים)")
            return tool_data
            
        except Exception as e:
            logger.error(f"שגיאה בחילוץ מ-{url}: {e}")
            return None
    
    def save_tool(self, tool_data):
        """שמירת כלי במסד נתונים"""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO ai_tools 
                (name, url, description, category, popularity, pricing, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                tool_data['name'],
                tool_data['url'],
                tool_data['description'],
                tool_data['category'],
                tool_data['popularity'],
                tool_data['pricing'],
                tool_data['tags']
            ))
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"שגיאה בשמירה: {e}")
    
    def scrape_page(self, page_path):
        """גרידת עמוד בודד"""
        url = self.base_url + page_path
        logger.info(f"🔍 גורד עמוד: {page_path}")
        
        html = self.get_page(url)
        if not html:
            return []
        
        tool_links = self.find_tool_links(html)
        logger.info(f"   נמצאו {len(tool_links)} קישורים")
        
        # בדוק גם pagination
        soup = BeautifulSoup(html, 'html.parser')
        next_links = soup.find_all('a', href=re.compile(r'/page/\d+'))
        
        for next_link in next_links[:5]:  # מקסימום 5 עמודים
            next_url = urljoin(url, next_link.get('href'))
            if next_url not in self.processed_urls:
                self.processed_urls.add(next_url)
                next_html = self.get_page(next_url)
                if next_html:
                    more_links = self.find_tool_links(next_html)
                    tool_links.extend(more_links)
        
        return tool_links
    
    def scrape_all(self):
        """גרידת כל האתר"""
        logger.info("🚀 מתחיל גרידה מלאה")
        
        all_tool_links = []
        
        # גרוד כל עמוד
        for page_path in self.main_pages:
            try:
                page_links = self.scrape_page(page_path)
                all_tool_links.extend(page_links)
            except Exception as e:
                logger.error(f"שגיאה בעמוד {page_path}: {e}")
                continue
        
        # הסר כפולים
        unique_links = list(set(all_tool_links))
        logger.info(f"📊 סך הכל קישורים ייחודיים: {len(unique_links)}")
        
        if len(unique_links) < 1000:
            logger.warning(f"⚠️ מספר קישורים נמוך: {len(unique_links)}")
        
        # גרוד כל כלי
        saved_count = 0
        filtered_count = 0
        
        for i, tool_url in enumerate(unique_links, 1):
            if i % 50 == 0:
                logger.info(f"📈 התקדמות: {i}/{len(unique_links)} ({saved_count} נשמרו)")
            
            if tool_url in self.processed_urls:
                continue
                
            self.processed_urls.add(tool_url)
            
            html = self.get_page(tool_url)
            if not html:
                continue
            
            tool_data = self.extract_tool_data(html, tool_url)
            if tool_data:
                self.save_tool(tool_data)
                self.scraped_tools.append(tool_data)
                saved_count += 1
            else:
                filtered_count += 1
        
        logger.info(f"🎉 גרידה הושלמה!")
        logger.info(f"✅ נשמרו: {saved_count} כלים")
        logger.info(f"🚫 נפסלו: {filtered_count} כלים")
        logger.info(f"❌ נכשלו: {len(self.failed_urls)} כלים")
        
        return self.scraped_tools
    
    def get_stats(self):
        """סטטיסטיקות"""
        self.cursor.execute('SELECT COUNT(*) FROM ai_tools')
        total = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT category, COUNT(*) FROM ai_tools WHERE category != "" GROUP BY category ORDER BY COUNT(*) DESC')
        categories = self.cursor.fetchall()
        
        self.cursor.execute('SELECT pricing, COUNT(*) FROM ai_tools WHERE pricing != "" GROUP BY pricing')
        pricing = self.cursor.fetchall()
        
        return {
            'total': total,
            'categories': categories,
            'pricing': pricing,
            'failed': len(self.failed_urls)
        }
    
    def close(self):
        """סגירה"""
        if self.conn:
            self.conn.close()

# הפעלה
if __name__ == "__main__":
    print("🚀 מתחיל גרידת AIxploria")
    print("⏱️  צפוי זמן: 30-60 דקות")
    print("💡 לעצירה: Ctrl+C")
    
    # מחק קובץ ישן
    if os.path.exists('ai_tools_full.db'):
        os.remove('ai_tools_full.db')
        print("🗑️  קובץ ישן נמחק")
    
    scraper = AIxploriaScraper()
    
    try:
        start_time = time.time()
        
        # גרידה
        tools = scraper.scrape_all()
        
        # סטטיסטיקות
        stats = scraper.get_stats()
        
        duration = (time.time() - start_time) / 60
        
        print(f"\n📊 תוצאות:")
        print(f"⏱️  זמן: {duration:.1f} דקות")
        print(f"🎯 כלים נשמרו: {stats['total']}")
        print(f"❌ כלים נכשלו: {stats['failed']}")
        
        if stats['total'] > 2000:
            print("🎉 מצוין! גרידה מוצלחת")
        elif stats['total'] > 1000:
            print("👍 טוב! גרידה סבירה")
        else:
            print("⚠️ נמוך מהצפוי")
        
        print(f"\n📂 קטגוריות:")
        for cat, count in stats['categories'][:8]:
            print(f"  • {cat}: {count}")
        
        print(f"\n💰 מחירים:")
        for price, count in stats['pricing']:
            print(f"  • {price}: {count}")
        
        # בדיקת קובץ
        if os.path.exists('ai_tools_full.db'):
            size = os.path.getsize('ai_tools_full.db') / 1024
            print(f"\n💾 קובץ: ai_tools_full.db ({size:.1f} KB)")
            
            if size > 1000:
                print("✅ גודל מצוין")
            elif size > 500:
                print("✅ גודל טוב")
            else:
                print("⚠️ גודל קטן")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ הופסק על ידי משתמש")
        stats = scraper.get_stats()
        print(f"📊 עד כה: {stats['total']} כלים")
        
    except Exception as e:
        print(f"\n❌ שגיאה: {e}")
        
    finally:
        scraper.close()
        print("✅ סיום")
