import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

def upload_image(file, folder="blog_images"):
    """
    Upload an image to Cloudinary
    
    Args:
        file: The uploaded file object
        folder: The folder to store the image in (default: blog_images)
    
    Returns:
        dict: Contains 'url' and 'public_id' of the uploaded image
    """
    try:
        # Upload the image
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="image",
            transformation=[
                {"width": 800, "height": 600, "crop": "limit", "quality": "auto"},
                {"fetch_format": "auto"}
            ]
        )
        
        return {
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'success': True
        }
    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        return {
            'url': None,
            'public_id': None,
            'success': False,
            'error': str(e)
        }

def delete_image(public_id):
    """
    Delete an image from Cloudinary
    
    Args:
        public_id: The public_id of the image to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"Error deleting from Cloudinary: {str(e)}")
        return False

def get_optimized_url(public_id, width=None, height=None, crop="limit"):
    """
    Get an optimized URL for an image
    
    Args:
        public_id: The public_id of the image
        width: Desired width
        height: Desired height
        crop: Crop mode (limit, fill, etc.)
    
    Returns:
        str: Optimized image URL
    """
    try:
        transformation = []
        if width or height:
            transformation.append({
                "width": width,
                "height": height,
                "crop": crop,
                "quality": "auto",
                "fetch_format": "auto"
            })
        
        return cloudinary.CloudinaryImage(public_id).build_url(transformation=transformation)
    except Exception as e:
        print(f"Error generating optimized URL: {str(e)}")
        return None
