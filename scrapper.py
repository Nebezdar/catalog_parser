import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

class ProductScraper:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')  # Убираем завершающий слэш
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
            product = {
                'название': soup.select_one('#pagetitle').text.strip() if soup.select_one('#pagetitle') else '',
                'артикул': soup.select_one('.catalog-element-article span').text.strip() if soup.select_one('.catalog-element-article span') else '',
                'описание': soup.select_one('.catalog-element-section-description').text.strip() if soup.select_one('.catalog-element-section-description') else '',
                'цена': soup.select_one('.catalog-element-price-discount').text.strip() if soup.select_one('.catalog-element-price-discount') else '',
                'характеристики': '',
                'url': product_url
            }
            
            # Собираем характеристики
            chars_table = soup.select('.catalog-element-section-property')
            characteristics = []
            for char in chars_table:
                name = char.select_one('.catalog-element-section-property-name')
                value = char.select_one('.catalog-element-section-property-value')
                if name and value:
                    characteristics.append(f"{name.text.strip()}: {value.text.strip()}")
            
            # Исправлено объединение строк
            product['характеристики'] = '\n'.join(characteristics)
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
        items = soup.select('.catalog-section-item')
        if not items:
            print("Товары не найдены")
            return

        total_items = len(items)
        print(f"Найдено товаров: {total_items}")

        for index, item in enumerate(items, 1):
            try:
                # Исправляем селектор для поиска ссылки (убираем пробел между классами)
                link = item.select_one('.section-item-name.intec-cl-text-hover')
                if not link:
                    # Попробуем альтернативный селектор
                    link = item.select_one('a[data-role="offer.link"]')
                    if not link:
                        print(f"Не найдена ссылка для товара {index}")
                        continue
                        
                href = link.get('href')
                if not href:
                    print(f"Не найден URL для товара {index}")
                    continue

                # Формируем правильный URL
                if href.startswith('/'):
                    product_url = f"{self.base_url}{href}"
                else:
                    product_url = f"{self.base_url}/{href}" 

                print(f"\nОбработка товара {index}/{total_items}")
                print(f"URL товара: {product_url}")
                
                product_data = self.parse_product(product_url)
                if product_data:
                    self.products.append(product_data)
                    print(f"✓ Собран товар: {product_data['название']}")
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
            
        # Проверяем существование файла
        try:
            existing_df = pd.read_csv(filename, encoding='utf-8-sig')
            # Объединяем существующие данные с новыми
            df = pd.concat([existing_df, pd.DataFrame(self.products)], ignore_index=True)
        except FileNotFoundError:
            # Если файл не существует, создаем новый
            df = pd.DataFrame(self.products)
        
        # Сохраняем объединенные данные
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\nДанные сохранены в {filename}")
        print(f"Всего товаров в файле: {len(df)}")
        print(f"Добавлено новых товаров: {len(self.products)}")

if __name__ == "__main__":
    base_url = "https://bdrosma.ru"
    
    scraper = ProductScraper(base_url)
    
    # Можно собирать данные с разных разделов
    scraper.parse_catalog('/catalog/manometry/')
    scraper.save_to_csv('manometry.csv')
    
    # Для другого раздела
    scraper.products = []  # Очищаем список перед новым сбором
    scraper.parse_catalog('/catalog/tsifrovye_monometry/')
    scraper.save_to_csv('manometry.csv')  # Данные добавятся в конец файла

    scraper.products = []  
    scraper.parse_catalog('/catalog/tsifrovye_manometry/')
    scraper.save_to_csv('manometry.csv')  

    scraper.products = []  
    scraper.parse_catalog('/catalog/naparomer/')
    scraper.save_to_csv('manometry.csv')  

    scraper.products = []  
    scraper.parse_catalog('/catalog/tsifrovye_monometry/')
    scraper.save_to_csv('manometry.csv')


    