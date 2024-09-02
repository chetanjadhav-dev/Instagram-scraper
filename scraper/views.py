from django.http import JsonResponse
from django.views import View
import instaloader
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import re

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
    text = pytesseract.image_to_string(image)
    
    # Replace line breaks and unwanted symbols
    text = text.replace('\n', ' ').replace("'", "")
    
    # Join multiple spaces into a single space
    text = " ".join(text.split())
    
    # Replace vertical bars with the letter 'I'
    text = text.replace('|', 'I')
    text = text.replace('-', '')
    
    # Filter out non-alphabetic symbols but keep spaces
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    # Define allowed 2-4 letter words
    allowed_short_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'his', 'her', 
                           'she', 'him', 'has', 'can', 'was', 'had', 'all', 'our', 'out',
                           'use', 'one', 'two', 'get', 'see', 'new', 'day', 'any', 'now',
                           'man', 'men', 'too', 'may', 'own', 'hold', 'this', 'that', 'with', 'have',
                           'from', 'were', 'they', 'been', 'will', 'them', 'more', 'when',
                           'what', 'make', 'like', 'such', 'self', 'care'}
    
    # Split the text into words
    words = text.split()
    
    # Filter non-word tokens but keep allowed short words
    meaningful_words = [word for word in words if len(word) > 4 or word.lower() in allowed_short_words]

    allow = False
    lowercase = len([word for word in meaningful_words if word.lower()])
    print(lowercase)

    if lowercase >= 3:
        filtered_text = " ".join(meaningful_words)
    else:
        filtered_text = " ".join([word for word in meaningful_words if word.upper()])
    
    return filtered_text


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
                extracted_texts[i] = {'post': post.url,
                                      'text': extracted_text}

            return JsonResponse({
                'profile_username': username,
                'post_count': len(post_urls),
                'extracted_texts': extracted_texts,
            })

        except instaloader.exceptions.ProfileNotExistsException:
            return JsonResponse({'error': f"Profile '{username}' does not exist."}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
