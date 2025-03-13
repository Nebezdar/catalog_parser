import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

class ProductScraper:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.products = []

    def get_page(self, url):
        try:
            print(f"Загрузка страницы: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Ошибка при получении страницы {url}: {e}")
            return None

    def parse_product(self, product_url):
        soup = self.get_page(product_url)
        if not soup:
            return None
        
        try:
            # Получаем название категории и артикул
            category = soup.select_one('.b-item-title h5')
            article = soup.select_one('.b-item-title h1')
            
            # Получаем описание
            description = soup.select_one('.b-text p')
            
            # Получаем характеристики
            specifications = soup.select_one('.b-text.b-text-table')
            
            product = {
                'категория': category.text.strip() if category else '',
                'артикул': article.text.strip() if article else '',
                'описание': description.text.strip() if description else '',
                'характеристики': specifications.text.strip() if specifications else '',
                'url': product_url,
                'новинка': 'да' if soup.select_one('.b-new') else 'нет'
            }
            
            return product
        except Exception as e:
            print(f"Ошибка при парсинге товара {product_url}: {e}")
            return None

    def parse_catalog(self, catalog_path):
        url = f"{self.base_url}{catalog_path}"
        soup = self.get_page(url)
        if not soup:
            return

        # Находим все товары в каталоге
        items = soup.select('.b-goods li')
        if not items:
            print("Товары не найдены")
            return

        total_items = len(items)
        print(f"Найдено товаров: {total_items}")

        for index, item in enumerate(items, 1):
            try:
                # Ищем ссылку на товар
                link = item.find('a')
                if not link:
                    print(f"Не найдена ссылка для товара {index}")
                    continue
                
                href = link.get('href')
                if not href:
                    print(f"Не найден URL для товара {index}")
                    continue

                # Формируем полный URL
                product_url = f"{self.base_url}{href}" if href.startswith('/') else href

                print(f"\nОбработка товара {index}/{total_items}")
                print(f"URL товара: {product_url}")
                
                product_data = self.parse_product(product_url)
                if product_data:
                    self.products.append(product_data)
                    print(f"✓ Собран товар: {product_data['артикул']}")
                else:
                    print(f"✗ Ошибка при сборе товара: {product_url}")
                
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"Ошибка при обработке товара {index}: {str(e)}")
                continue

    def save_to_csv(self, filename='products.csv'):
        if not self.products:
            print("Нет данных для сохранения")
            return
            
        new_df = pd.DataFrame(self.products)
        
        try:
            # Пытаемся прочитать существующий файл
            existing_df = pd.read_csv(filename, encoding='utf-8-sig')
            
            # Проверяем на дубликаты по артикулу и названию
            existing_items = set(existing_df['артикул'].dropna()) | set(existing_df['название'].dropna())
            new_items = set(new_df['артикул'].dropna()) | set(new_df['название'].dropna())
            
            # Находим только новые товары
            duplicates = len(new_items & existing_items)
            if duplicates > 0:
                print(f"\nНайдено дубликатов: {duplicates}")
                
                # Фильтруем новые товары
                new_df = new_df[~((new_df['артикул'].isin(existing_df['артикул'])) | 
                                 (new_df['название'].isin(existing_df['название'])))]
                
            # Объединяем с существующими данными
            df = pd.concat([existing_df, new_df], ignore_index=True)
            
        except FileNotFoundError:
            print("\nСоздание нового файла")
            df = new_df
        
        # Сохраняем результат
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"Данные сохранены в {filename}")
        print(f"Всего товаров в файле: {len(df)}")
        print(f"Добавлено новых товаров: {len(new_df)}")
        print(f"Пропущено дубликатов: {len(self.products) - len(new_df)}")

if __name__ == "__main__":
    base_url = "https://manotom.com/"
    
    scraper = ProductScraper(base_url)
    
    # Список разделов для парсинга
    sections = [
        '/catalog/mekh/manometry-strelochnye-s-kanalom-peredachi-dannykh/',
        '/catalog/mekh/tochnye/tochnye/',
        '/catalog/mekh/tochnye/tekhnicheskie/',
        '/catalog/mekh/tochnye/ammiachnye/',
        '/catalog/mekh/tochnye/korrozionnostoykie/',
        '/catalog/mekh/tochnye/manometry-korrozionnostoykie-v-bezopasnom-korpuseе/',
        '/catalog/mekh/tochnye/manometry-s-zashchitoy-ot-peregruzki/',
        '/catalog/mekh/tochnye/vibroustoychivye/',
        '/catalog/mekh/tochnye/manometry-vibroustoychivye-korrozionnostoykie/',
        '/catalog/mekh/tochnye/electro-signal/',
        '/catalog/mekh/tochnye/electro-signal-vzr/',
        '/catalog/mekh/tochnye/zhd/',
        '/catalog/mekh/tochnye/sudovye/',
        '/catalog/mekh/tochnye/foodprom/',
        '/catalog/mekh/tochnye/dif/',
        '/catalog/mekh/tochnye/vacuum/',
        
        # Добавьте другие разделы по необходимости
    ]
    
    for section in sections:
        scraper.parse_catalog(section)
        scraper.save_to_csv('manometry_new.csv')
        scraper.products = []  # Очищаем список перед следующим разделом


