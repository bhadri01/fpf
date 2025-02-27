from app.core.config import settings
from app.core.minio import s3_client
from PIL import Image
import hashlib
import random
import io

def generate_pixel_avatar(email, size=6, scale=32):
        """Generate a pixelated avatar and upload to MinIO, returning the URL."""
        random.seed(str(email))

        # Generate a single color for the avatar
        main_color = (random.randint(50, 200), random.randint(
            50, 200), random.randint(50, 200))

        # Generate a mirrored pattern
        pixels = [[random.choice([0, 1]) for _ in range(size // 2)]
                  for _ in range(size)]
        for row in pixels:
            row.extend(reversed(row))

        # Create image
        img = Image.new("RGB", (size, size), "white")
        for y in range(size):
            for x in range(size):
                color = main_color if pixels[y][x] == 1 else (255, 255, 255)
                img.putpixel((x, y), color)

        # Scale up for better visibility
        img = img.resize((size * scale, size * scale), Image.NEAREST)

        # Generate filename based on email hash
        email_hash = hashlib.md5(email.encode()).hexdigest()
        filename = f"profiles/{email_hash}.png"

        # Save to in-memory buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Upload to MinIO
        s3_client.put_object(
            Bucket=settings.minio_bucket,
            Key=filename,
            Body=img_buffer,
            ContentType="image/png",
            ACL="public-read"
        )

        # Return MinIO URL
        return f"/{filename}"