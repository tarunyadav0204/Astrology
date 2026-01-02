import os
from datetime import datetime
from PIL import Image
import io

class LocalStorageManager:
    def __init__(self):
        self.upload_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(self.upload_dir, exist_ok=True)
        self.base_url = 'http://localhost:8001/uploads'
    
    def upload_image(self, file_content: bytes, filename: str, content_type: str):
        """Save image locally for testing"""
        date_path = datetime.now().strftime('%Y/%m')
        upload_path = os.path.join(self.upload_dir, date_path)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, filename)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return {
            'filename': f"{date_path}/{filename}",
            'public_url': f"{self.base_url}/{date_path}/{filename}",
            'local_path': file_path
        }
    
    def upload_chart(self, chart_data: bytes, filename: str):
        """Save chart locally for testing"""
        return self.upload_image(chart_data, filename, 'image/png')

# Use local storage for testing
try:
    from google.cloud import storage
    storage_manager = CloudStorageManager()
except Exception as e:
    print(f"Using local storage: {e}")
    storage_manager = LocalStorageManager()