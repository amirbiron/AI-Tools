import sqlite3
import json
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIToolsSemanticSearch:
    def __init__(self, db_path='ai_tools_full.db'):
        self.db_path = db_path
        self.model = None
        self.tools_data = []
        self.embeddings = None
        
        # טען מודל embedding (קטן ומהיר)
        logger.info("🤖 טוען מודל עברית/אנגלית...")
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ מודל נטען בהצלחה")
        except Exception as e:
            logger.error(f"שגיאה בטעינת מודל: {e}")
            raise
        
        self.load_tools_from_db()
        self.setup_search_index()
    
    def load_tools_from_db(self):
        """טעינת כלים ממסד הנתונים"""
        logger.info("📊 טוען כלים ממסד הנתונים...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT name, url, description, category, popularity, pricing, tags 
                FROM ai_tools 
                WHERE description IS NOT NULL AND description != ""
                ORDER BY name
            ''')
            
            rows = cursor.fetchall()
            
            for row in rows:
                tool = {
                    'name': row[0] or '',
                    'url': row[1] or '', 
                    'description': row[2] or '',
                    'category': row[3] or '',
                    'popularity': row[4] or '',
                    'pricing': row[5] or '',
                    'tags': row[6] or ''
                }
                self.tools_data.append(tool)
            
            conn.close()

        except sqlite3.DatabaseError as e:
            logger.error(f"Database error loading data: {e}")
            raise
        except Exception as e:
            logger.error(f"שגיאה בטעינת נתונים: {e}")
            # ניסיון עם נתונים דמה אם מסד הנתונים לא זמין
            self.tools_data = [
                {
                    'name': 'ChatGPT',
                    'url': 'https://www.aixploria.com/en/chatgpt/',
                    'description': 'Advanced AI chatbot for conversations and text generation.',
                    'category': 'Text Generation',
                    'popularity': '+15840',
                    'pricing': 'freemium',
                    'tags': 'chat, AI, conversation'
                },
                {
                    'name': 'MidJourney',
                    'url': 'https://www.aixploria.com/en/midjourney/',
                    'description': 'AI image generator that creates stunning artwork from text prompts.',
                    'category': 'Image Generation',
                    'popularity': '+12453',
                    'pricing': 'paid',
                    'tags': 'image, art, generation'
                }
            ]
        
        logger.info(f"✅ נטענו {len(self.tools_data)} כלי AI")
        
        if len(self.tools_data) == 0:
            logger.warning("⚠️ לא נמצאו כלים - משתמש בנתונים דמה")
    
    def create_search_text(self, tool):
        """יצירת טקסט מאוחד לחיפוש"""
        parts = [
            tool['name'],
            tool['description'],
            tool['category'],
            tool['tags']
        ]
        
        # נקה וחבר
        search_text = ' '.join([part.strip() for part in parts if part.strip()])
        
        # נקה מתווים מיוחדים
        search_text = re.sub(r'[^\w\s]', ' ', search_text)
        search_text = re.sub(r'\s+', ' ', search_text).strip()
        
        return search_text
    
    def setup_search_index(self):
        """בניית אינדקס חיפוש"""
        logger.info("🔧 בונה אינדקס חיפוש סמנטי...")
        
        # יצור טקסט לחיפוש לכל כלי
        search_texts = []
        for tool in self.tools_data:
            search_text = self.create_search_text(tool)
            search_texts.append(search_text)
        
        # יצור embeddings
        logger.info("⚡ יוצר embeddings...")
        try:
            self.embeddings = self.model.encode(search_texts)
            logger.info(f"✅ אינדקס חיפוש מוכן עם {len(self.tools_data)} כלים")
        except Exception as e:
            logger.error(f"שגיאה ביצירת embeddings: {e}")
            # יצור embeddings דמה
            self.embeddings = np.random.rand(len(self.tools_data), 384)
    
    def preprocess_query(self, query):
        """עיבוד מקדים של השאלה"""
        # המרה לאנגלית של מילים נפוצות בעברית
        hebrew_to_english = {
            'צ\'אט': 'chat',
            'צאט': 'chat', 
            'בוט': 'bot',
            'תמונה': 'image',
            'תמונות': 'image',
            'וידאו': 'video',
            'וידיו': 'video',
            'סרטון': 'video',
            'טקסט': 'text',
            'כתיבה': 'writing',
            'עיצוב': 'design',
            'יצירה': 'generation create',
            'חינמי': 'free',
            'בחינם': 'free',
            'בתשלום': 'paid',
            'עריכה': 'editing',
            'קוד': 'code',
            'תכנות': 'programming code',
            'אתר': 'website',
            'לוגו': 'logo',
            'מוסיקה': 'music',
            'קול': 'voice audio',
            'תרגום': 'translation',
            'שפה': 'language'
        }
        
        # החלף מילים בעברית
        for hebrew, english in hebrew_to_english.items():
            query = query.replace(hebrew, english)
        
        # נקה
        query = re.sub(r'[^\w\s]', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def search(self, query, top_k=10):
        """חיפוש סמנטי"""
        if not query.strip():
            return self.get_random_tools(top_k)
        
        # עבד שאלה
        processed_query = self.preprocess_query(query)
        logger.info(f"🔍 מחפש: '{query}' -> '{processed_query}'")
        
        try:
            # יצור embedding לשאלה
            query_embedding = self.model.encode([processed_query])
            
            # חשב דמיון
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # קבל אינדקסים של התוצאות הטובות ביותר
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # הכן תוצאות
            results = []
            for i, idx in enumerate(top_indices):
                if idx >= len(self.tools_data):
                    continue
                    
                tool = self.tools_data[idx].copy()
                tool['relevance_score'] = float(similarities[idx])
                tool['rank'] = i + 1
                
                # חשב נקודות פופולריות
                popularity_bonus = 0
                if tool['popularity']:
                    try:
                        pop_num = int(tool['popularity'].replace('+', '').replace(',', ''))
                        popularity_bonus = min(pop_num / 10000, 0.1)  # מקסימום 0.1 בונוס
                    except:
                        pass
                
                tool['final_score'] = similarities[idx] + popularity_bonus
                
                # רק תוצאות עם ציון סביר
                if tool['final_score'] > 0.1:
                    results.append(tool)
            
            # מיין לפי ציון סופי
            results.sort(key=lambda x: x['final_score'], reverse=True)
            
            logger.info(f"✅ נמצאו {len(results)} תוצאות")
            return results
            
        except Exception as e:
            logger.error(f"שגיאה בחיפוש: {e}")
            return self.get_random_tools(top_k)
    
    def search_by_category(self, category, top_k=20):
        """חיפוש לפי קטגוריה"""
        results = []
        
        for i, tool in enumerate(self.tools_data):
            if category.lower() in tool['category'].lower():
                tool_copy = tool.copy()
                tool_copy['rank'] = len(results) + 1
                tool_copy['relevance_score'] = 1.0
                tool_copy['final_score'] = 1.0
                results.append(tool_copy)
                
                if len(results) >= top_k:
                    break
        
        return results
    
    def get_categories(self):
        """קבלת רשימת קטגוריות"""
        categories = set()
        for tool in self.tools_data:
            if tool['category']:
                categories.add(tool['category'])
        
        return sorted(list(categories))
    
    def get_random_tools(self, count=10):
        """כלים אקראיים"""
        import random
        
        if count >= len(self.tools_data):
            base_tools = self.tools_data
        else:
            base_tools = random.sample(self.tools_data, count)

        tools = []
        for i, tool in enumerate(base_tools):
            tool_copy = tool.copy()
            tool_copy['rank'] = i + 1
            tool_copy['relevance_score'] = 1.0
            tool_copy['final_score'] = 1.0
            tools.append(tool_copy)
        
        return tools
    
    def get_popular_tools(self, top_k=20):
        """כלים פופולריים"""
        tools_with_pop = []
        
        for tool in self.tools_data:
            if tool['popularity']:
                try:
                    pop_num = int(tool['popularity'].replace('+', '').replace(',', ''))
                    tool_copy = tool.copy()
                    tool_copy['pop_num'] = pop_num
                    tools_with_pop.append(tool_copy)
                except:
                    pass
        
        # מיין לפי פופולריות
        tools_with_pop.sort(key=lambda x: x['pop_num'], reverse=True)
        
        results = []
        for i, tool in enumerate(tools_with_pop[:top_k]):
            tool['rank'] = i + 1
            tool['relevance_score'] = 1.0
            tool['final_score'] = 1.0
            results.append(tool)
        
        return results
    
    def save_index(self, path='search_index.pkl'):
        """שמירת אינדקס"""
        try:
            data = {
                'tools_data': self.tools_data,
                'embeddings': self.embeddings.tolist() if self.embeddings is not None else None
            }
            
            with open(path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"💾 אינדקס נשמר ב-{path}")
            return True
        except Exception as e:
            logger.error(f"שגיאה בשמירת אינדקס: {e}")
            return False
    
    def load_index(self, path='search_index.pkl'):
        """טעינת אינדקס"""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.tools_data = data['tools_data']
            if data['embeddings']:
                self.embeddings = np.array(data['embeddings'])
            
            logger.info(f"📁 אינדקס נטען מ-{path}")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בטעינת אינדקס: {e}")
            return False

# דוגמאות לשימוש
if __name__ == "__main__":
    print("🚀 יוצר מנוע חיפוש AI...")
    
    try:
        # יצור מנוע חיפוש
        search_engine = AIToolsSemanticSearch()
        
        # דוגמאות חיפוש
        test_queries = [
            "כלי ליצירת תמונות",
            "צ'אט בוט עם AI", 
            "עריכת וידאו",
            "יצירת לוגו",
            "תרגום שפות",
            "כתיבת קוד",
            "חינמי"
        ]
        
        print("\n🔍 בדיקת חיפושים:")
        
        for query in test_queries:
            print(f"\n📝 שאלה: '{query}'")
            results = search_engine.search(query, top_k=3)
            
            for result in results:
                score = result['final_score']
                print(f"  • {result['name']} (ציון: {score:.3f})")
                print(f"    📂 {result['category']} | 💰 {result['pricing']}")
                if result['description']:
                    print(f"    📝 {result['description'][:100]}...")
        
        # שמור אינדקס
        search_engine.save_index()
        
        print(f"\n✅ מנוע חיפוש מוכן עם {len(search_engine.tools_data)} כלים!")
        print("💡 עכשיו אפשר לבנות ממשק משתמש")
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")
        print("💡 הקוד ירוץ עם נתונים דמה אם מסד הנתונים לא זמין")
