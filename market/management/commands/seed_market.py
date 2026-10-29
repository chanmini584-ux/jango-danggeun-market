from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from market.models import Product


class Command(BaseCommand):
    help = "Add sample listings once. Sample sellers cannot log in."

    @transaction.atomic
    def handle(self, *args, **options):
        seller, created = User.objects.get_or_create(username="sample_neighbor", defaults={"first_name": "동네이웃"})
        if created:
            seller.set_unusable_password()
            seller.save()
        legacy_titles = {
            "데일리 캔버스 토트백": "데일리 백팩 상태 좋아요",
            "홈카페 에스프레소 머신": "홈카페 원두 미개봉",
            "원목 라운지 의자, 상태 좋아요": "패브릭 원목 의자, 상태 좋아요",
            "27인치 모니터 판매합니다": "일체형 데스크톱 판매합니다",
        }
        for old_title, new_title in legacy_titles.items():
            Product.objects.filter(seller=seller, title=old_title, image_url__startswith="/static/market/products/").update(title=new_title)
        rows = [
            ("패브릭 원목 의자, 상태 좋아요", 45000, "가구/인테리어", "chair", "서초동"),
            ("여행용 미러리스 카메라", 220000, "디지털기기", "camera", "반포동"),
            ("따뜻한 빛의 스탠드 조명", 18000, "가구/인테리어", "lamp", "서초동"),
            ("노이즈 캔슬링 무선 헤드폰", 85000, "디지털기기", "headphones", "역삼동"),
            ("주말 산책용 자전거", 110000, "스포츠/레저", "bicycle", "서초동"),
            ("주말에 읽기 좋은 책 세 권", 12000, "도서", "books", "방배동"),
            ("홈카페 원두 미개봉", 65000, "생활가전", "coffee", "반포동"),
            ("잘 자라는 초록 식물 나눔", 0, "기타", "plant", "서초동"),
            ("데일리 백팩 상태 좋아요", 15000, "의류/잡화", "bag", "역삼동"),
            ("일체형 데스크톱 판매합니다", 90000, "디지털기기", "monitor", "방배동"),
            ("거의 새 운동화 250", 28000, "의류/잡화", "shoes", "서초동"),
            ("작업용 원목 책상", 55000, "가구/인테리어", "desk", "반포동"),
        ]
        count = 0
        for index, (title, price, category, image, region) in enumerate(rows):
            product, made = Product.objects.get_or_create(seller=seller, title=title, defaults={
                "price": price, "category": category, "region": "서울 " + region,
                "image_url": f"/static/market/products/photos/{image}.jpg",
                "content": "과제 시연용 샘플 상품입니다.\n\n아껴 사용한 물건을 필요한 이웃에게 전하고 싶어요. 사용감은 조금 있지만 상태는 좋습니다. 가까운 곳에서 직거래를 희망해요. 편하게 채팅 주세요!",
                "negotiable": True, "status": "reserved" if index == 4 else "selling"})
            if not made and product.image_url == f"/static/market/products/{image}.svg":
                product.image_url = f"/static/market/products/photos/{image}.jpg"
                product.save(update_fields=["image_url"])
            count += made
        self.stdout.write(self.style.SUCCESS(f"Created {count} sample listings (existing listings preserved)."))
