import os
import uuid
from django.core.files.storage import default_storage


class ImageUploadError(Exception):
    """An upload failure safe to display in the product form."""


def upload_product_image(uploaded_file, user_id):
    try:
        return _upload_product_image(uploaded_file, user_id)
    except Exception as error:
        raise ImageUploadError("사진 업로드에 실패했습니다. 저장 공간 또는 이미지 서비스 설정을 확인하고 다시 시도해주세요.") from error


def _upload_product_image(uploaded_file, user_id):
    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
    path = f"products/{user_id}/{uuid.uuid4().hex}.{extension}"
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        from supabase import create_client
        client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
        client.storage.from_("product-images").upload(path, uploaded_file.read(), {
            "content-type": uploaded_file.content_type, "upsert": "false"})
        return client.storage.from_("product-images").get_public_url(path)
    return default_storage.url(default_storage.save(path, uploaded_file))
