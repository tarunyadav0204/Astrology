from google.cloud import storage
import os
from datetime import datetime
from PIL import Image
import io

class CloudStorageManager:
    def __init__(self):
        self.client = storage.Client()
        self.images_bucket = self.client.bucket('astroroshni-blog-images')
        self.charts_bucket = self.client.bucket('astroroshni-blog-charts')
        self.image_base_url = 'https://storage.googleapis.com/astroroshni-blog-images'
        self.chart_base_url = 'https://storage.googleapis.com/astroroshni-blog-charts'
    
    def upload_image(self, file_content: bytes, filename: str, content_type: str):
        """Upload image to Cloud Storage with optimization"""
        # Generate unique filename with date path
        date_path = datetime.now().strftime('%Y/%m')
        unique_filename = f"uploads/{date_path}/{filename}"
        
        # Upload original
        blob = self.images_bucket.blob(unique_filename)
        blob.upload_from_string(file_content, content_type=content_type)
        blob.make_public()
        
        # Create optimized WebP version
        if content_type.startswith('image/'):
            webp_filename = f"uploads/{date_path}/optimized/{filename.rsplit('.', 1)[0]}.webp"
            self._create_webp_version(file_content, webp_filename)
        
        return {
            'filename': unique_filename,
            'public_url': f"{self.image_base_url}/{unique_filename}",
            'gcs_path': f"gs://{self.images_bucket.name}/{unique_filename}"
        }
    
    def upload_chart(self, chart_data: bytes, filename: str):
        """Upload generated chart to Cloud Storage"""
        date_path = datetime.now().strftime('%Y/%m')
        unique_filename = f"generated/{date_path}/{filename}"
        
        blob = self.charts_bucket.blob(unique_filename)
        blob.upload_from_string(chart_data, content_type='image/png')
        blob.make_public()
        
        return {
            'filename': unique_filename,
            'public_url': f"{self.chart_base_url}/{unique_filename}",
            'gcs_path': f"gs://{self.charts_bucket.name}/{unique_filename}"
        }
    
    def _create_webp_version(self, image_content: bytes, webp_filename: str):
        """Create optimized WebP version of image"""
        try:
            image = Image.open(io.BytesIO(image_content))
            
            # Resize if too large
            if image.width > 1200:
                ratio = 1200 / image.width
                new_height = int(image.height * ratio)
                image = image.resize((1200, new_height), Image.Resampling.LANCZOS)
            
            # Convert to WebP
            webp_buffer = io.BytesIO()
            image.save(webp_buffer, format='WebP', quality=85, optimize=True)
            webp_content = webp_buffer.getvalue()
            
            # Upload WebP version
            blob = self.images_bucket.blob(webp_filename)
            blob.upload_from_string(webp_content, content_type='image/webp')
            blob.make_public()
            
        except Exception as e:
            print(f"Error creating WebP version: {e}")

storage_manager = CloudStorageManager()