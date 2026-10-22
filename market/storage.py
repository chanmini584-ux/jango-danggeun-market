import os
import uuid

from supabase import create_client


BUCKET_NAME = "product-images"


def get_supabase():

    # .env에 키가 없어도 사이트 전체가 멈추지 않도록, 업로드할 때 클라이언트를 만든다
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )


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

    return (
        supabase.storage
        .from_(BUCKET_NAME)
        .get_public_url(file_path)
    )
