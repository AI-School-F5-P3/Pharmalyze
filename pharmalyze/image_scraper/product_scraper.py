# image_scraper/product_scraper.py
import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from django.conf import settings
from .models import Product, ProductInfo
from product_search.vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductInfoScraper:
    def __init__(self, driver, base_save_path=None):
        self.driver = driver
        self.base_save_path = base_save_path or Path(settings.MEDIA_ROOT) / 'product_info'
        self.vector_store = VectorStore()
        self._ensure_save_directory()

    def _ensure_save_directory(self):
        """Create necessary directories if they don't exist"""
        self.base_save_path.mkdir(parents=True, exist_ok=True)
        for category in ['quemagrasas', 'celulitis', 'dieta', 'drenante', 
                        'edulcorantes', 'inhibidores_de_absorcion', 
                        'laxantes', 'saciante', 'uncategorized']:
            (self.base_save_path / category).mkdir(exist_ok=True)

    def _extract_product_info(self, product_url):
        """Extract detailed product information from product page"""
        try:
            self.driver.get(product_url)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract product information
            product_info = {
                'name': '',
                'description': '',
                'usage': '',
                'composition': '',
                'price_per_unit': '',
                'expert_advice': '',
                'expert_info': {}
            }

            # Extract main product description
            description_div = soup.find('div', id='content-description')
            if description_div:
                product_info['description'] = description_div.get_text(strip=True)

            # Extract usage information
            usage_div = soup.find('div', id='content-instructions')
            if usage_div:
                product_info['usage'] = usage_div.get_text(strip=True)

            # Extract composition
            composition_div = soup.find('div', id='content-composition')
            if composition_div:
                product_info['composition'] = composition_div.get_text(strip=True)

            # Extract price per unit
            price_div = soup.find('div', id='content-price-per-100')
            if price_div:
                product_info['price_per_unit'] = price_div.get_text(strip=True)

            # Extract expert advice
            expert_div = soup.find('div', id='content-professional-advice')
            if expert_div:
                product_info['expert_advice'] = expert_div.get_text(strip=True)

            # Extract expert information
            expert_profile = soup.find('div', class_='OurExpert')
            if expert_profile:
                product_info['expert_info'] = {
                    'name': expert_profile.find('strong').get_text(strip=True) if expert_profile.find('strong') else '',
                    'title': expert_profile.find('p', class_='pf-color-grayplus').get_text(strip=True) if expert_profile.find('p', class_='pf-color-grayplus') else ''
                }

            return product_info

        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
            return None

    def _save_product_info(self, product_info, category, product_name):
        """Save product information to file and database"""
        try:
            # Normalize product name for filename
            safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            
            # Save to file
            category_path = self.base_save_path / category
            file_path = category_path / f"{safe_name}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(product_info, f, ensure_ascii=False, indent=2)

            # Save to database
            product = Product.objects.create(
                name=product_name,
                description=product_info['description'],
                category=category,
                metadata=product_info
            )

            # Add to vector store
            self.vector_store.add_product(
                product_id=product.id,
                product_data={
                    'name': product_name,
                    'description': product_info['description'],
                    'category': category,
                    'usage': product_info['usage'],
                    'expert_advice': product_info['expert_advice']
                }
            )

            logger.info(f"Saved product info for {product_name}")
            return True

        except Exception as e:
            logger.error(f"Error saving product info: {e}")
            return False

    def scrape_product_info(self, product_url, category, product_name):
        """Main method to scrape and save product information"""
        try:
            product_info = self._extract_product_info(product_url)
            if product_info:
                return self._save_product_info(product_info, category, product_name)
            return False
        except Exception as e:
            logger.error(f"Error in scrape_product_info: {e}")
            return False