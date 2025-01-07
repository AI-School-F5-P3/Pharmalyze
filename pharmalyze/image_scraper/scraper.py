# image_scraper/scrape.py
import asyncio
import aiohttp
import logging
import traceback
import unicodedata
import re
from pathlib import Path
from urllib.parse import urljoin
from PIL import Image
import io
from django.conf import settings
from .product_scraper import ProductInfoScraper


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import chromedriver_autoinstaller
from django.core.cache import cache

# Configuration Constants
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
DEFAULT_DOWNLOAD_TIMEOUT = 15
MAX_FILENAME_LENGTH = 200

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RobustWebScraper:
    def __init__(self, 
                 base_url='https://www.promofarma.com/dietetica/adelgazar', 
                 max_images_per_page=64, 
                 max_pages=40,
                 progress_callback=None):
        # Install ChromeDriver and get its path
        chromedriver_path = chromedriver_autoinstaller.install()

        # Chrome options configuration
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Initialize driver
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Scraper configuration
        self.base_url = base_url
        self.max_images_per_page = max_images_per_page
        self.max_pages = max_pages
        
        # Updated directory structure
        self.base_images_dir = Path(settings.MEDIA_ROOT) / 'images' / 'Dietetica' / 'Adelgazar'
        
        # Comprehensive and Flexible Category Mapping
        self.category_mapping = {
            'dietetica': {
                'adelgazar': {
                    'quemagrasas': ['quemagrasas', 'fat burners', 'fat burning'],
                    'celulitis': ['celulitis', 'cellulite'],
                    'dieta': ['dieta', 'diet', 'weight loss'],
                    'drenante': ['drenante', 'draining', 'water retention'],
                    'edulcorantes': ['edulcorantes', 'stevia', 'sweeteners'],
                    'inhibidores_de_absorcion': {
                        'azucares': ['sugar blockers', 'sugar absorption'],
                        'grasas': ['fat blockers', 'fat absorption']
                    },
                    'laxantes': ['laxantes', 'laxative'],
                    'saciante': ['saciante', 'appetite suppressant', 'appetite control']
                }
            }
        }
        
        # Create directory structure
        self._create_directory_structure()
        
        # Track processed products
        self.processed_products = set()
        
        self.progress_callback = progress_callback
        self.total_images = 0
        self.processed_images = 0
        self.product_scraper = ProductInfoScraper(self.driver)

    def _create_directory_structure(self):
        """Create the full directory structure for image storage"""
        try:
            # Create base directory
            self.base_images_dir.mkdir(parents=True, exist_ok=True)
            
            # Create main category directories
            main_categories = ['quemagrasas', 'celulitis', 'dieta', 'drenante', 
                            'edulcorantes', 'inhibidores_de_absorcion', 
                            'laxantes', 'saciante', 'uncategorized']
            
            for main_cat in main_categories:
                category_path = self.base_images_dir / main_cat
                category_path.mkdir(exist_ok=True)
                
                # Create subcategories for inhibidores_de_absorcion
                if main_cat == 'inhibidores_de_absorcion':
                    subcategories = ['azucares', 'grasas']
                    for subcat in subcategories:
                        (category_path / subcat).mkdir(exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directory structure: {e}")

    def _normalize_text(self, text):
        """
        Normalize text by removing accents, converting to lowercase, and handling special characters.
        
        :param text: Input text to normalize
        :return: Normalized text
        """
        if not text:
            return ''
        
        # Normalize unicode characters
        normalized = unicodedata.normalize('NFKD', str(text).lower())
        # Remove non-ASCII characters and replace spaces with underscores
        cleaned = re.sub(r'[^\w\s-]', '', normalized).replace(' ', '_')
        return cleaned

    def _determine_category(self, category_data):
        """
        Determine the most appropriate category based on multiple category attributes.
        
        :param category_data: Dictionary of category attributes
        :return: Tuple of (category, subcategory)
        """
        # Extract category information with additional normalization
        category_candidates = [
            self._normalize_text(category_data.get('category_name_three', '')),
            self._normalize_text(category_data.get('category_name_two', '')),
            self._normalize_text(category_data.get('category_name_one', ''))
        ]

        # Comprehensive multilingual category mapping
        category_mapping = {
            'dietetica': {
                'adelgazar': {
                    'quemagrasas': {
                        'aliases': ['quemagrasas', 'fat burners', 'fat burning', 'aufnahmeblocker', 'fatburners'],
                        'sub_categories': {}
                    },
                    'celulitis': {
                        'aliases': ['celulitis', 'cellulite'],
                        'sub_categories': {}
                    },
                    'dieta': {
                        'aliases': ['dieta', 'diet', 'weight loss'],
                        'sub_categories': {}
                    },
                    'drenante': {
                        'aliases': ['drenante', 'draining', 'water retention'],
                        'sub_categories': {}
                    },
                    'edulcorantes': {
                        'aliases': ['edulcorantes', 'stevia', 'sweeteners'],
                        'sub_categories': {}
                    },
                    'inhibidores_de_absorcion': {
                        'aliases': ['inhibidores de absorcion', 'absorption inhibitors'],
                        'sub_categories': {
                            'azucares': {
                                'aliases': ['azucares', 'sugar', 'sugar blockers', 'sugar absorption']
                            },
                            'grasas': {
                                'aliases': ['grasas', 'fat', 'fat blockers', 'fat absorption', 'aufnahmeblocker']
                            }
                        }
                    },
                    'laxantes': {
                        'aliases': ['laxantes', 'laxative'],
                        'sub_categories': {}
                    },
                    'saciante': {
                        'aliases': ['saciante', 'appetite suppressant', 'appetite control'],
                        'sub_categories': {}
                    }
                }
            }
        }

        # Normalize input categories
        def normalize_category(category):
            return self._normalize_text(str(category)) if category else ''

        category_candidates = [
            normalize_category(category_data.get('category_name_three', '')),
            normalize_category(category_data.get('category_name_two', '')),
            normalize_category(category_data.get('category_name_one', '')),
            normalize_category(category_data.get('category', ''))
        ]
        
        # Traverse category mapping with enhanced matching
        for candidate in category_candidates:
            # Check main categories first
            for main_cat, cat_details in category_mapping.get('dietetica', {}).get('adelgazar', {}).items():
                # Check main category aliases
                if candidate in [self._normalize_text(alias) for alias in cat_details.get('aliases', [])]:
                    return main_cat, None

                # Check subcategories
                if 'sub_categories' in cat_details:
                    for subcat_key, subcat_details in cat_details['sub_categories'].items():
                        # Check subcategory aliases
                        if candidate in [self._normalize_text(alias) for alias in subcat_details.get('aliases', [])]:
                            return main_cat, subcat_key

        # Fallback to specific mapping for known translations
        translation_map = {
            'aufnahmeblocker': ('inhibidores_de_absorcion', 'grasas'),
            'aufnahme blocker': ('inhibidores_de_absorcion', 'grasas')
        }

        for translated_cat, (main_cat, subcat) in translation_map.items():
            if any(translated_cat in normalize_category(cat) for cat in category_candidates):
                return main_cat, subcat

        return 'uncategorized', None

    async def _download_image(self, session, image_data):
        """
        Async image download with comprehensive error handling and image validation
        
        :param session: aiohttp ClientSession
        :param image_data: Dictionary containing image metadata
        :return: Tuple (image_content, file_extension, error_message)
        """
        try:
            # Extract image URL and verify
            img_url = image_data.get('src')
            if not img_url:
                return None, None, "No image URL provided"

            # Skip SVG files
            if img_url.lower().endswith('.svg'):
                logger.warning(f"Skipping SVG file: {img_url}")
                return None, None, "SVG files not supported"

            # Download image with extended error handling
            headers = {
                'User-Agent': USER_AGENT,
                'Accept': 'image/webp,image/jpeg,image/png,image/*'
            }
            
            async with session.get(img_url, headers=headers, timeout=DEFAULT_DOWNLOAD_TIMEOUT) as response:
                # Verify successful download
                if response.status != 200:
                    return None, None, f"Download failed with status {response.status}"

                # Read image content
                image_content = await response.read()
                
            # Enhanced image validation and debugging
            try:
                image_buffer = io.BytesIO(image_content)
                
                # Add more robust image identification
                try:
                    img = Image.open(image_buffer)
                    # Force load the entire image
                    img.load()
                except Exception as identify_error:
                    # Log more detailed error information
                    logger.error(f"Image identification error: {identify_error}")
                    logger.error(f"Image content length: {len(image_content)}")
                    logger.error(f"First 100 bytes: {image_content[:100]}")
                    
                    # Try alternative methods
                    try:
                        # Check if it's a valid web image type
                        import imghdr
                        image_type = imghdr.what(None, h=image_content)
                        if image_type:
                            logger.info(f"Image type detected: {image_type}")
                            # Save with correct extension
                            file_ext = f'.{image_type}'
                    except Exception as imghdr_error:
                        logger.error(f"imghdr error: {imghdr_error}")
                    
                    return None, None, "Invalid image format"
                
                # Convert to RGB to ensure compatibility
                rgb_img = img.convert('RGB')
                
                # Determine file extension
                file_ext_map = {
                    'JPEG': '.jpg',
                    'PNG': '.png',
                    'GIF': '.gif',
                    'WEBP': '.webp'
                }
                file_ext = file_ext_map.get(img.format, '.jpg')
                
                # Save to BytesIO to get standardized image
                output_buffer = io.BytesIO()
                rgb_img.save(output_buffer, format='JPEG')
                return output_buffer.getvalue(), '.jpg', None
            
            except Exception as img_error:
                logger.error(f"Comprehensive image validation error: {img_error}")
                logger.error(f"Error type: {type(img_error)}")
                return None, None, "Invalid image format"

        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading {image_data.get('src')}")
            return None, None, "Download timeout"
        except Exception as e:
            logger.error(f"Download error for {image_data.get('src')}: {e}")
            return None, None, str(e)

    async def _process_image_download(self, session, image_data):
        """
        Comprehensive image download and processing
        
        :param session: aiohttp ClientSession
        :param image_data: Dictionary containing image metadata
        :return: Boolean indicating download success
        """
        try:
            # Download image content
            img_content, file_ext, error = await self._download_image(session, image_data)
            if error or not img_content:
                logger.warning(f"Image download failed: {error}")
                return False

            # Determine category with improved categorization
            category_data = {
                'category_name_one': image_data.get('category_one', ''),
                'category_name_two': image_data.get('category_two', ''),
                'category_name_three': image_data.get('category_three', '')
            }
            category, subcategory = self._determine_category(category_data)

            # Generate sanitized filename
            base_filename = self._normalize_text(image_data.get('product_name', 'unknown_product'))
            full_filename = f"{base_filename}{file_ext}"

            # Construct save path with fallback
            try:
                if subcategory and subcategory != category:
                    save_path = self.base_images_dir / category / subcategory / full_filename
                else:
                    save_path = self.base_images_dir / category / full_filename

                # Ensure directory exists
                save_path.parent.mkdir(parents=True, exist_ok=True)

                # Save image
                save_path.write_bytes(img_content)
                
                logger.info(f"Successfully saved: {save_path}")
                
                # After successful image download, scrape product info
                product_url = image_data.get('product_url')
                if product_url:
                    self.product_scraper.scrape_product_info(
                        product_url=product_url,
                        category=category,
                        product_name=image_data.get('product_name', 'unknown_product')
                    )
                return True
            
            except Exception as save_error:
                logger.error(f"Error saving image: {save_error}")
                return False

        except Exception as e:
            logger.error(f"Image/product processing error: {e}")
            return False

    def scrape_images(self):
        total_successful_downloads = 0
        
        try:
            current_url = self.base_url
            
            # First pass to count total images
            for page_num in range(1, self.max_pages + 1):
                self.driver.get(current_url)
                image_containers = self.driver.find_elements(By.CSS_SELECTOR, 'article.product-card')
                self.total_images += len(image_containers[:self.max_images_per_page])
                
                try:
                    next_page = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        f'li.page-item:not(.active) a.page-link[data-page="{page_num + 1}"]'
                    )
                except Exception:
                    break
            
            # Reset for actual scraping
            current_url = self.base_url
            self.processed_images = 0
            
            if self.progress_callback:
                self.progress_callback(0, self.total_images)
            
            for page_num in range(1, self.max_pages + 1):
                logger.info(f"Scraping Page {page_num}")
                
                # Navigate to page
                self.driver.get(current_url)
                
                # Handle potential cookie popup (if present)
                try:
                    # Wait for and click cookie accept button if it exists
                    cookie_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
                    )
                    cookie_button.click()
                except Exception:
                    # No cookie popup or unable to click - continue scraping
                    logger.info("No cookie popup found or unable to interact")
                
                # Wait for image containers
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.product-card'))
                )
                
                image_containers = self.driver.find_elements(By.CSS_SELECTOR, 'article.product-card')
                logger.info(f"Found {len(image_containers)} image containers")
                
                # Async image download
                async def download_page_images():
                    async with aiohttp.ClientSession() as session:
                        tasks = []
                        for idx, container in enumerate(image_containers[:self.max_images_per_page], 1):
                            try:
                                # Get product URL (NEW CODE)
                                try:
                                    product_link = container.find_element(By.CSS_SELECTOR, 'a[data-testid="product-link"]')
                                    product_url = product_link.get_attribute('href')
                                except Exception as e:
                                    logger.error(f"Error getting product URL: {e}")
                                    product_url = None # Set to None if not found

                                # Extract product name with fallback (Existing code)
                                try:
                                    product_name = container.get_attribute('data-name')
                                except Exception:
                                    try:
                                        product_name_elem = container.find_element(By.CSS_SELECTOR, 'h3[itemprop="name"]')
                                        product_name = product_name_elem.text
                                    except Exception:
                                        product_name = f"unknown_product_{page_num}_{idx}"

                                # Extract image URL with lazy loading handling (Existing code)
                                try:
                                    img_elem = container.find_element(By.CSS_SELECTOR, 'img.prodimg')
                                    img_url = (
                                        img_elem.get_attribute('data-src') or 
                                        img_elem.get_attribute('src')
                                    )
                                    if (not img_url or 
                                        img_url.lower().endswith('.svg') or 
                                        'animated/logo.svg' in img_url):
                                        logger.warning(f"Skipping invalid image URL: {img_url}")
                                        continue
                                        
                                    # Prepare comprehensive image data for download (Modified)
                                    image_data = {
                                        'src': img_url,
                                        'product_name': f"{product_name}_page{page_num}_{idx}",
                                        'category_one': container.get_attribute('data-category-name-one'),
                                        'category_two': container.get_attribute('data-category-name-two'),
                                        'category_three': container.get_attribute('data-category-name-three'),
                                        'product_url': product_url # Add product URL to image data
                                    }

                                    # Check for duplicate product (Existing code)
                                    if product_name not in self.processed_products:
                                        self.processed_products.add(product_name)

                                        task = asyncio.create_task(
                                            self._process_image_download(session, image_data)
                                        )
                                        tasks.append(task)
                                    
                                    if self.progress_callback:
                                        self.processed_images += 1
                                        self.progress_callback(self.processed_images, self.total_images)

                                except Exception as img_err:
                                    logger.error(f"Image extraction error: {img_err}")

                            except Exception as container_err:
                                logger.error(f"Container processing error: {container_err}")
                        return await asyncio.gather(*tasks)

                # Run async downloads
                results = asyncio.run(download_page_images())
                
                # Count and log successful downloads
                page_downloads = sum(results)
                total_successful_downloads += page_downloads
                logger.info(f"Successfully downloaded {page_downloads} images on page {page_num}")
                
                # Find next page
                try:
                    next_page_link = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        'li.page-item:not(.active) a.page-link[data-page="{}"]'.format(page_num + 1)
                    )
                    current_url = urljoin(self.base_url, next_page_link.get_attribute('href'))
                except Exception:
                    logger.info("No more pages to scrape")
                    break
        
        except Exception as e:
            logger.error(f"Main scraping error: {e}")
            traceback.print_exc()
        
        finally:
            self.driver.quit()
        
        logger.info(f"Total successful downloads: {total_successful_downloads}")
        return total_successful_downloads
    
    def cleanup(self):
        try:
            self.driver.quit()
        except:
            pass
        finally:
            cache.delete('scraping_in_progress')

def main():
    scraper = RobustWebScraper()
    scraper.scrape_images()

if __name__ == "__main__":
    main()