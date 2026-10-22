import os
import uuid

from supabase import create_client


BUCKET_NAME = "product-images"


class ImageUploadError(Exception):
    """사진 업로드 실패. 메시지는 폼에 그대로 보여준다."""


def get_supabase():

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ImageUploadError(
            "사진 업로드 설정이 아직 안 되어 있습니다. "
            "사진 없이 등록하거나, .env에 SUPABASE_URL과 "
            "SUPABASE_SERVICE_ROLE_KEY를 넣은 뒤 서버를 다시 켜주세요."
        )

    # .env에 키가 없어도 사이트 전체가 멈추지 않도록, 업로드할 때 클라이언트를 만든다
    return create_client(url, key)


def upload_product_image(uploaded_file, user_id):

    supabase = get_supabase()

    extension = (
        uploaded_file.name
        .split(".")[-1]
        .lower()
    )

    file_name = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    file_path = (
        f"products/{user_id}/{file_name}"
    )

    try:
        supabase.storage.from_(
            BUCKET_NAME
        ).upload(
            path=file_path,
            file=uploaded_file.read(),
            file_options={
                "content-type": uploaded_file.content_type,
                "upsert": "false",
            }
        )

    except Exception as error:
        raise ImageUploadError(
            "사진 업로드에 실패했습니다. Supabase에 product-images 버킷이 "
            f"있는지와 키가 맞는지 확인해주세요. ({error})"
        ) from error

    return (
        supabase.storage
        .from_(BUCKET_NAME)
        .get_public_url(file_path)
    )
