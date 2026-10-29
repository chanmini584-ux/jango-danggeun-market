from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Profile


class AccountFlowTests(TestCase):
    def signup_data(self):
        return {"username": "markettester", "name": "Tester",
                "birth_date": "2000-01-01", "phone": "01012345678",
                "password1": "Market-test-4839!", "password2": "Market-test-4839!"}

    def test_public_pages(self):
        for name in ("main", "signup", "login"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_signup_logout_and_login(self):
        data = self.signup_data()
        self.assertRedirects(self.client.post(reverse("signup"), data), reverse("main"))
        user = User.objects.get(username=data["username"])
        self.assertEqual(Profile.objects.get(user=user).phone, data["phone"])
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.client.get(reverse("logout"))
        self.assertIn("_auth_user_id", self.client.session)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.post(reverse("login"), {
            "username": data["username"], "password": data["password1"]}), reverse("main"))

    def test_duplicate_phone_is_rejected(self):
        data = self.signup_data()
        self.client.post(reverse("signup"), data)
        self.client.post(reverse("logout"))
        data["username"] = "anotheruser"
        response = self.client.post(reverse("signup"), data)
        self.assertIn("phone", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_login(self):
        response = self.client.post(reverse("login"), {"username": "missing", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertTrue(list(response.context["messages"]))


from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from .models import Product, Wishlist, ChatRoom, ChatMessage
from PIL import Image
from io import BytesIO
import tempfile


class MarketplaceTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user("seller", password="Valid-pass-123!")
        self.buyer = User.objects.create_user("buyer", password="Valid-pass-123!")
        self.other = User.objects.create_user("other", password="Valid-pass-123!")
        self.product = Product.objects.create(seller=self.seller, title="테스트 의자", content="원목 의자입니다", region="서울 서초동", price=30000, category="가구/인테리어")

    def test_search_filters_and_empty_results(self):
        for params, count in [({"q": "의자"}, 1), ({"region": "부산"}, 0), ({"category": "도서"}, 0)]:
            response = self.client.get(reverse("main"), params)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["products"].paginator.count, count)
        self.product.status = "sold"
        self.product.save()
        self.assertEqual(self.client.get(reverse("main"), {"available": "1"}).context["products"].paginator.count, 0)

    def test_create_requires_login_and_local_image_upload(self):
        self.assertEqual(self.client.get(reverse("product_create")).status_code, 302)
        self.client.force_login(self.seller)
        buffer = BytesIO()
        Image.new("RGB", (20, 20), "orange").save(buffer, "PNG")
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            response = self.client.post(reverse("product_create"), {"title": "새 상품", "content": "설명", "region": "서초동", "price": 1000, "category": "기타", "image": SimpleUploadedFile("test.png", buffer.getvalue(), content_type="image/png")})
            self.assertEqual(response.status_code, 302)
            self.assertTrue(Product.objects.get(title="새 상품").image_url.startswith("/media/products/"))

    def test_owner_permissions_and_status(self):
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.post(reverse("product_update", args=[self.product.pk]), {}).status_code, 403)
        self.assertEqual(self.client.post(reverse("product_delete", args=[self.product.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("product_status", args=[self.product.pk]), {"status": "sold"}).status_code, 404)
        self.client.force_login(self.seller)
        response = self.client.get(reverse("product_detail", args=[self.product.pk]))
        self.assertContains(response, "상태 변경")
        self.assertEqual(self.client.post(reverse("product_status", args=[self.product.pk]), {"status": "invalid"}).status_code, 400)
        self.client.post(reverse("product_status", args=[self.product.pk]), {"status": "sold"})
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, "sold")

    def test_wishlist_and_personal_lists(self):
        self.client.force_login(self.buyer)
        url = reverse("wishlist_toggle", args=[self.product.pk])
        self.client.post(url)
        self.assertEqual(Wishlist.objects.count(), 1)
        self.assertEqual(self.client.get(reverse("main"), {"mode": "wished"}).context["products"].paginator.count, 1)
        self.assertEqual(self.client.get(reverse("main"), {"mode": "mine"}).context["products"].paginator.count, 0)
        self.client.post(url)
        self.assertFalse(Wishlist.objects.exists())

    def test_chat_rooms_are_unique_and_private(self):
        self.client.force_login(self.buyer)
        url = reverse("chat_start", args=[self.product.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(ChatRoom.objects.count(), 1)
        room = ChatRoom.objects.get()
        self.assertContains(self.client.get(reverse("chat_room", args=[room.pk])), self.product.title)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse("chat_room", args=[room.pk])).status_code, 403)
        self.assertEqual(list(self.client.get(reverse("chat_list")).context["rooms"]), [])

    def test_owner_can_edit_and_delete(self):
        self.client.force_login(self.seller)
        response = self.client.post(reverse("product_update", args=[self.product.pk]), {"title": "수정 제목", "content": "설명", "region": "서초동", "price": 2000, "category": "기타"})
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.title, "수정 제목")
        self.client.post(reverse("product_delete", args=[self.product.pk]))
        self.assertFalse(Product.objects.exists())


from django.test import TransactionTestCase
from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from .routing import websocket_urlpatterns
from django.contrib.auth.models import AnonymousUser


class RealtimeChatTests(TransactionTestCase):
    def test_websocket_permissions_broadcast_and_persistence(self):
        seller = User.objects.create_user("ws_seller")
        buyer = User.objects.create_user("ws_buyer")
        outsider = User.objects.create_user("ws_outsider")
        product = Product.objects.create(seller=seller, title="채팅 테스트", content="설명", price=100, region="서초")
        room = ChatRoom.objects.create(product=product, seller=seller, buyer=buyer)

        async def scenario():
            clients = []
            try:
                for user in (AnonymousUser(), outsider):
                    rejected = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f"/ws/chat/{room.pk}/")
                    rejected.scope["user"] = user
                    connected, _ = await rejected.connect()
                    self.assertFalse(connected)
                    await rejected.disconnect()
                for user in (seller, buyer):
                    client = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f"/ws/chat/{room.pk}/")
                    client.scope["user"] = user
                    connected, _ = await client.connect()
                    self.assertTrue(connected)
                    clients.append(client)
                await clients[1].send_json_to({"message": "안녕하세요! 거래 가능할까요?"})
                for client in clients:
                    payload = await client.receive_json_from()
                    self.assertEqual(payload["message"], "안녕하세요! 거래 가능할까요?")
                    self.assertEqual(payload["username"], buyer.username)
                self.assertEqual(await sync_to_async(ChatMessage.objects.count)(), 1)
                await clients[1].send_json_to({"message": " "})
                await clients[1].send_json_to({"message": 123})
                await clients[1].send_json_to({"message": "x" * 2001})
                self.assertTrue(await clients[0].receive_nothing(timeout=0.1))
            finally:
                for client in clients:
                    await client.disconnect()
        async_to_sync(scenario)()


from unittest.mock import patch
from .storage import ImageUploadError


class UploadFailureTests(TestCase):
    def test_upload_failure_shows_form_error_without_saving(self):
        user = User.objects.create_user("uploadtester")
        self.client.force_login(user)
        product = Product.objects.create(seller=user, title="Existing", content="Description", region="Seoul", price=100, category="기타")
        for route in (reverse("product_create"), reverse("product_update", args=[product.pk])):
            buffer = BytesIO()
            Image.new("RGB", (10, 10)).save(buffer, "PNG")
            with patch("market.views.upload_product_image", side_effect=ImageUploadError("사진 저장 실패")):
                response = self.client.post(route, {"title": "Changed", "content": "Description", "region": "Seoul", "price": 200, "category": "기타", "image": SimpleUploadedFile("photo.png", buffer.getvalue(), content_type="image/png")})
            self.assertEqual(response.status_code, 200)
            self.assertIn("image", response.context["form"].errors)
            self.assertEqual(Product.objects.count(), 1)
            product.refresh_from_db()
            self.assertEqual(product.title, "Existing")
