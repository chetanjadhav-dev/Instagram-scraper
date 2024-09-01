from django.http import JsonResponse
from django.views import View
import instaloader
import pytesseract
from PIL import Image
import requests
from io import BytesIO

# Initialize Instaloader
L = instaloader.Instaloader()

# Set Tesseract executable path if necessary
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust the path as needed

def download_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        return img
    else:
        raise Exception(f"Failed to download image. Status code: {response.status_code}")

def extract_text_from_image(image):
    # Use pytesseract to extract text
    text = pytesseract.image_to_string(image).replace('\n', ' ').replace('\'', "")
    text = ",".join(text.split('  ')[:-1]).replace("\'", "").replace('|', 'I')
    return text

class ScrapeAndExtractView(View):
    def get(self, request, username, max_posts):
        try:
            # Load the Instagram profile
            profile = instaloader.Profile.from_username(L.context, username)
            post_urls = []
            extracted_texts = {}

            # Loop through the posts and process images
            for i, post in enumerate(profile.get_posts()):
                if i >= max_posts:
                    break
                post_urls.append(post.url)

                # Download image and extract text
                img = download_image(post.url)
                extracted_text = extract_text_from_image(img)
                extracted_texts[i] = {'text': extracted_text}

            return JsonResponse({
                'profile_username': username,
                'post_count': len(post_urls),
                'extracted_texts': extracted_texts,
            })

        except instaloader.exceptions.ProfileNotExistsException:
            return JsonResponse({'error': f"Profile '{username}' does not exist."}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
