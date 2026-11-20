
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import User
from products.models import ProductReview
from .models import Notification

from .models import Product, Category,Cart,CartItem,Order,OrderItem,StockMovement,Payment

User = get_user_model()


class ProductAPITestCase(APITestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )

        self.normal_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='user123'
        )

        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic products'
        )

        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            slug='laptop',
            description='Test laptop',
            price='50000.00',
            stock_quantity=10
        )

    def test_product_list_public_access(self):
        url = reverse('product-list-create')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_admin_can_create_product(self):
        self.client.force_authenticate(user=self.admin_user)

        url = reverse('product-list-create')

        data = {
            'name': 'Mobile',
            'slug': 'mobile',
            'category': self.category.id,
            'description': 'Smartphone',
            'price': '25000.00',
            'stock_quantity': 5,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
    def test_normal_user_cannot_create_product(self):
        self.client.force_authenticate(user=self.normal_user)

        url = reverse('product-list-create')

        data = {
            'name': 'Tablet',
            'slug': 'tablet',
            'category': self.category.id,
            'description': 'Android tablet',
            'price': '15000.00',
            'stock_quantity': 5
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        self.assertEqual(Product.objects.count(), 1)
    def test_product_detail_public_access(self):
        url = reverse(
            'product-detail',
            kwargs={'pk': self.product.id}
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data['name'],
            'Laptop'
        )
    def test_admin_can_update_product(self):
        self.client.force_authenticate(user=self.admin_user)

        url = reverse(
            'product-detail',
            kwargs={'pk': self.product.id}
        )

        data = {
            'price': '45000.00'
        }

        response = self.client.patch(url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.product.refresh_from_db()

        self.assertEqual(
            str(self.product.price),
            '45000.00'
        )
    def test_normal_user_cannot_update_product(self):
        self.client.force_authenticate(user=self.normal_user)

        url = reverse(
            'product-detail',
            kwargs={'pk': self.product.id}
        )

        data = {
            'price': '30000.00'
        }

        response = self.client.patch(url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        self.product.refresh_from_db()

        self.assertEqual(
            str(self.product.price),
            '50000.00'
        )
    def test_admin_can_delete_product(self):
        self.client.force_authenticate(user=self.admin_user)

        url = reverse(
            'product-detail',
            kwargs={'pk': self.product.id}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertEqual(Product.objects.count(), 0)
    def test_normal_user_cannot_delete_product(self):
        self.client.force_authenticate(user=self.normal_user)

        url = reverse(
            'product-detail',
            kwargs={'pk': self.product.id}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        self.assertTrue(
            Product.objects.filter(id=self.product.id).exists()
        )
    def test_unauthenticated_user_cannot_create_product(self):
        self.client.force_authenticate(user=None)

        url = reverse('product-list-create')

        data = {
            'name': 'Keyboard',
            'slug': 'keyboard',
            'category': self.category.id,
            'description': 'Wireless keyboard',
            'price': '2000.00',
            'stock_quantity': 10
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertEqual(Product.objects.count(), 1)
    def test_unauthenticated_user_cannot_update_product(self):
        self.client.force_authenticate(user=None)

        url = reverse(
            'product-detail',
            kwargs={'pk': self.product.id}
        )

        data = {
            'price': '35000.00'
        }

        response = self.client.patch(url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.product.refresh_from_db()

        self.assertEqual(
            str(self.product.price),
            '50000.00'
        )
    def test_unauthenticated_user_cannot_delete_product(self):
        self.client.force_authenticate(user=None)

        url = reverse(
            'product-detail',
            kwargs={'pk': self.product.id}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertTrue(
            Product.objects.filter(id=self.product.id).exists()
        )
    
    # CATEGORY API TESTS

    def test_category_list_public_access(self):
        url = reverse('category-list-create')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_category_detail_public_access(self):
        url = reverse(
            'category-detail',
            kwargs={'pk': self.category.id}
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Electronics')

    def test_admin_can_create_category(self):
        self.client.force_authenticate(user=self.admin_user)

        url = reverse('category-list-create')

        data = {
            'name': 'Clothing',
            'slug': 'clothing',
            'description': 'Clothing products'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)

    def test_normal_user_cannot_create_category(self):
        self.client.force_authenticate(user=self.normal_user)

        url = reverse('category-list-create')

        data = {
            'name': 'Books',
            'slug': 'books',
            'description': 'Book products'
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        self.assertEqual(Category.objects.count(), 1)

    def test_unauthenticated_user_cannot_create_category(self):
        url = reverse('category-list-create')

        data = {
            'name': 'Furniture',
            'slug': 'furniture',
            'description': 'Furniture products'
        }

        response = self.client.post(url, data)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertEqual(Category.objects.count(), 1)

    def test_admin_can_update_category(self):
        self.client.force_authenticate(user=self.admin_user)

        url = reverse(
            'category-detail',
            kwargs={'pk': self.category.id}
        )

        data = {
            'name': 'Updated Electronics'
        }

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.category.refresh_from_db()

        self.assertEqual(self.category.name, 'Updated Electronics')

    def test_normal_user_cannot_update_category(self):
        self.client.force_authenticate(user=self.normal_user)

        url = reverse(
            'category-detail',
            kwargs={'pk': self.category.id}
        )

        response = self.client.patch(
            url,
            {'name': 'Updated Category'}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        self.category.refresh_from_db()

        self.assertEqual(self.category.name, 'Electronics')

    def test_unauthenticated_user_cannot_update_category(self):
        url = reverse(
            'category-detail',
            kwargs={'pk': self.category.id}
        )

        response = self.client.patch(
            url,
            {'name': 'Updated Category'}
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.category.refresh_from_db()

        self.assertEqual(self.category.name, 'Electronics')

    def test_admin_cannot_delete_category_with_products(self):
        self.client.force_authenticate(user=self.admin_user)

        url = reverse(
            'category-detail',
            kwargs={'pk': self.category.id}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertTrue(
            Category.objects.filter(id=self.category.id).exists()
        )
    def test_admin_can_delete_empty_category(self):
        self.client.force_authenticate(user=self.admin_user)

        empty_category = Category.objects.create(
            name='Books',
            slug='books',
            description='Book products'
        )

        url = reverse(
            'category-detail',
            kwargs={'pk': empty_category.id}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Category.objects.filter(id=empty_category.id).exists()
        )

    def test_normal_user_cannot_delete_category(self):
        self.client.force_authenticate(user=self.normal_user)

        url = reverse(
            'category-detail',
            kwargs={'pk': self.category.id}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        self.assertTrue(
            Category.objects.filter(id=self.category.id).exists()
        )

    def test_unauthenticated_user_cannot_delete_category(self):
        url = reverse(
            'category-detail',
            kwargs={'pk': self.category.id}
        )

        response = self.client.delete(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertTrue(
            Category.objects.filter(id=self.category.id).exists()
        )

class CartAPITestCase(APITestCase):
    def setUp(self):

        self.user = User.objects.create_user(
            username='cartuser',
            email='cartuser@example.com',
            password='Test@12345'
        )

        self.other_user = User.objects.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='Test@12345'
        )

        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            slug='laptop',
            price=2500,
            discount_price=1999,
            stock_quantity=10,
            is_active=True
        )

        self.add_url = reverse('add-to-cart')
        self.cart_url = reverse('cart-detail')

        self.client.force_authenticate(user=self.user)

    # 1. View empty cart

    def test_view_empty_cart(self):

        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(len(response.data['items']), 0)

    # 2. Add product to cart

    def test_add_product_to_cart(self):

        response = self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 2
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        self.assertEqual(cart_item.quantity, 2)

    # 3. Add same product again

    def test_add_same_product_again(self):

        self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 2
            }
        )

        response = self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 3
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        self.assertEqual(cart_item.quantity, 5)

    # 4. Prevent quantity exceeding stock

    def test_add_product_exceeding_stock(self):

        response = self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 11
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 5. Prevent combined quantity exceeding stock

    def test_add_existing_product_exceeding_stock(self):

        self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 6
            }
        )

        response = self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 5
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        self.assertEqual(cart_item.quantity, 6)

    # 6. Prevent adding inactive product

    def test_add_inactive_product(self):

        self.product.is_active = False
        self.product.save()

        response = self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 1
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 7. Update cart item quantity

    def test_update_cart_item_quantity(self):

        self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 2
            }
        )

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        url = reverse(
            'cart-item-detail',
            kwargs={'pk': cart_item.id}
        )

        response = self.client.patch(
            url,
            {'quantity': 4}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cart_item.refresh_from_db()

        self.assertEqual(cart_item.quantity, 4)

    # 8. Prevent updating quantity exceeding stock

    def test_update_quantity_exceeding_stock(self):

        self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 2
            }
        )

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        url = reverse(
            'cart-item-detail',
            kwargs={'pk': cart_item.id}
        )

        response = self.client.patch(
            url,
            {'quantity': 15}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 9. Remove cart item

    def test_remove_cart_item(self):

        self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 2
            }
        )

        cart_item = CartItem.objects.get(
            cart__user=self.user,
            product=self.product
        )

        url = reverse(
            'cart-item-detail',
            kwargs={'pk': cart_item.id}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(
            CartItem.objects.filter(id=cart_item.id).exists()
        )

    # 10. Prevent accessing another user's cart item

    def test_user_cannot_update_other_users_cart_item(self):

        other_cart = Cart.objects.create(user=self.other_user)

        cart_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=2
        )

        url = reverse(
            'cart-item-detail',
            kwargs={'pk': cart_item.id}
        )

        response = self.client.patch(
            url,
            {'quantity': 3}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 11. Prevent unauthenticated cart access

    def test_unauthenticated_user_cannot_access_cart(self):

        self.client.force_authenticate(user=None)

        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 12. Verify cart total and subtotal

    def test_cart_total_calculation(self):

        self.client.post(
            self.add_url,
            {
                'product_id': self.product.id,
                'quantity': 2
            }
        )

        response = self.client.get(self.cart_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['total_items'], 2)

        self.assertEqual(
            response.data['total_price'],
            Decimal('3998.00')
        )
         

    def test_cart_total_calculation(self):
        self.client.force_authenticate(user=self.user)

        self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': self.product.id,
                'quantity': 2
            },
            format='json'
        )

        response = self.client.get(reverse('cart-detail'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_items'], 2)
        self.assertEqual(
            response.data['total_price'],
            Decimal('3998.00')
        )

class OrderAPITestCase(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username='orderuser',
            email='orderuser@example.com',
            password='Test@12345'
        )

        self.other_user = User.objects.create_user(
            username='otherorderuser',
            email='otherorderuser@example.com',
            password='Test@12345'
        )

        self.admin_user = User.objects.create_user(
            username='orderadmin',
            email='orderadmin@example.com',
            password='Test@12345',
            is_staff=True
        )

        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            slug='laptop',
            description='Test Laptop',
            price=Decimal('2500.00'),
            discount_price=Decimal('1999.00'),
            stock_quantity=10,
            is_active=True
        )

        self.place_order_url = reverse('place-order')
        self.order_list_url = reverse('order-list')

        self.shipping_address = (
            'House No 10, Trivandrum, Kerala, India'
        )

        self.client.force_authenticate(user=self.user)

    def add_product_to_cart(self, quantity=2):

        return self.client.post(
            reverse('add-to-cart'),
            {
                'product_id': self.product.id,
                'quantity': quantity
            },
            format='json'
        )

    def create_order(self, user=None, order_status='pending'):

        user = user or self.user

        return Order.objects.create(
            user=user,
            shipping_address=self.shipping_address,
            total_amount=Decimal('3998.00'),
            status=order_status
        )

    # 1. Place order successfully
    def test_place_order_successfully(self):

        self.add_product_to_cart(quantity=2)

        response = self.client.post(
            self.place_order_url,
            {'shipping_address': self.shipping_address},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        self.product.refresh_from_db()

        self.assertEqual(self.product.stock_quantity, 8)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(StockMovement.objects.count(), 1)

    # 2. Place order with empty cart
    def test_place_order_with_empty_cart(self):

        response = self.client.post(
            self.place_order_url,
            {'shipping_address': self.shipping_address},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    # 3. Place order with insufficient stock
    def test_place_order_with_insufficient_stock(self):

        cart = Cart.objects.create(user=self.user)

        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=11
        )

        response = self.client.post(
            self.place_order_url,
            {'shipping_address': self.shipping_address},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

        self.product.refresh_from_db()

        self.assertEqual(self.product.stock_quantity, 10)
        self.assertEqual(CartItem.objects.count(), 1)

    # 4. List logged-in user's orders
    def test_list_user_orders(self):

        self.create_order()

        self.create_order(user=self.other_user)

        response = self.client.get(self.order_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        orders = response.data.get('results', response.data)

        self.assertEqual(len(orders), 1)

    # 5. Retrieve order details
    def test_retrieve_order_details(self):

        order = self.create_order()

        response = self.client.get(
            reverse('order-detail', kwargs={'pk': order.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')

    # 6. Prevent access to another user's order
    def test_user_cannot_access_other_users_order(self):

        order = self.create_order(user=self.other_user)

        response = self.client.get(
            reverse('order-detail', kwargs={'pk': order.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 7. Cancel order and restore stock
    def test_cancel_order_and_restore_stock(self):

        self.product.stock_quantity = 8
        self.product.save()

        order = self.create_order()

        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=Decimal('1999.00'),
            quantity=2
        )

        response = self.client.post(
            reverse('cancel-order', kwargs={'pk': order.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(order.status, 'cancelled')
        self.assertEqual(self.product.stock_quantity, 10)

        self.assertTrue(
            StockMovement.objects.filter(
                product=self.product,
                adjustment_type='add',
                quantity=2
            ).exists()
        )

    # 8. Prevent cancelling an already cancelled order
    def test_cancel_already_cancelled_order(self):

        order = self.create_order(order_status='cancelled')

        response = self.client.post(
            reverse('cancel-order', kwargs={'pk': order.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 9. Prevent cancelling a shipped order
    def test_cancel_shipped_order(self):

        order = self.create_order(order_status='shipped')

        response = self.client.post(
            reverse('cancel-order', kwargs={'pk': order.pk})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 10. Admin can update order status
    def test_admin_can_update_order_status(self):

        order = self.create_order()

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            reverse('update-order-status', kwargs={'pk': order.pk}),
            {'status': 'confirmed'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()

        self.assertEqual(order.status, 'confirmed')

    # 11. Normal user cannot update order status
    def test_normal_user_cannot_update_order_status(self):

        order = self.create_order()

        response = self.client.patch(
            reverse('update-order-status', kwargs={'pk': order.pk}),
            {'status': 'confirmed'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # 12. Reject invalid order status transition
    def test_invalid_order_status_transition(self):

        order = self.create_order(order_status='pending')

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            reverse('update-order-status', kwargs={'pk': order.pk}),
            {'status': 'shipped'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()

        self.assertEqual(order.status, 'pending')

class PaymentAPITestCase(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username='paymentuser',
            email='paymentuser@example.com',
            password='Test@12345'
        )

        self.other_user = User.objects.create_user(
            username='otherpaymentuser',
            email='otherpaymentuser@example.com',
            password='Test@12345'
        )

        self.order = Order.objects.create(
            user=self.user,
            shipping_address='Trivandrum, Kerala, India',
            total_amount=Decimal('3998.00'),
            status='pending'
        )

        self.other_order = Order.objects.create(
            user=self.other_user,
            shipping_address='Kochi, Kerala, India',
            total_amount=Decimal('2500.00'),
            status='pending'
        )

        self.create_payment_url = reverse('create-payment')
        self.payment_history_url = reverse('payment-history')

        self.client.force_authenticate(user=self.user)

    def create_payment(self, order=None, payment_method='upi'):

        order = order or self.order

        return self.client.post(
            self.create_payment_url,
            {
                'order': order.id,
                'payment_method': payment_method
            },
            format='json'
        )

    # 1. Create payment successfully
    def test_create_payment_successfully(self):

        response = self.create_payment()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)

        payment = Payment.objects.first()

        self.assertEqual(payment.payment_status, 'pending')
        self.assertEqual(payment.amount, Decimal('3998.00'))
        self.assertEqual(payment.payment_method, 'upi')

    # 2. Prevent payment for another user's order
    def test_cannot_create_payment_for_other_users_order(self):

        response = self.create_payment(order=self.other_order)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Payment.objects.count(), 0)

    # 3. Prevent payment for an already paid order
    def test_prevent_duplicate_successful_payment(self):

        Payment.objects.create(
            order=self.order,
            payment_method='upi',
            payment_status='successful',
            amount=self.order.total_amount,
            transaction_id='TXN-EXISTING-123'
        )

        response = self.create_payment()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 4. Prevent payment for an order that cannot be paid
    def test_payment_not_allowed_for_shipped_order(self):

        self.order.status = 'shipped'
        self.order.save()

        response = self.create_payment()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Payment.objects.count(), 0)

    # 5. Verify successful payment
    def test_verify_payment_successfully(self):

        payment = Payment.objects.create(
            order=self.order,
            payment_method='upi',
            amount=self.order.total_amount
        )

        response = self.client.post(
            reverse('verify-payment', kwargs={'pk': payment.pk}),
            {'result': 'success'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment.refresh_from_db()
        self.order.refresh_from_db()

        self.assertEqual(payment.payment_status, 'successful')
        self.assertIsNotNone(payment.transaction_id)
        self.assertEqual(self.order.status, 'confirmed')

    # 6. Verify failed payment
    def test_verify_failed_payment(self):

        payment = Payment.objects.create(
            order=self.order,
            payment_method='card',
            amount=self.order.total_amount
        )

        response = self.client.post(
            reverse('verify-payment', kwargs={'pk': payment.pk}),
            {'result': 'failure'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment.refresh_from_db()

        self.assertEqual(payment.payment_status, 'failed')
        self.assertIsNone(payment.transaction_id)

    # 7. Prevent verifying an already processed payment
    def test_prevent_repeated_payment_verification(self):

        payment = Payment.objects.create(
            order=self.order,
            payment_method='upi',
            payment_status='successful',
            amount=self.order.total_amount,
            transaction_id='TXN-ALREADY-PAID'
        )

        response = self.client.post(
            reverse('verify-payment', kwargs={'pk': payment.pk}),
            {'result': 'success'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 8. Prevent accessing another user's payment
    def test_cannot_verify_other_users_payment(self):

        payment = Payment.objects.create(
            order=self.other_order,
            payment_method='upi',
            amount=self.other_order.total_amount
        )

        response = self.client.post(
            reverse('verify-payment', kwargs={'pk': payment.pk}),
            {'result': 'success'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 9. View payment history
    def test_payment_history(self):

        Payment.objects.create(
            order=self.order,
            payment_method='upi',
            amount=self.order.total_amount
        )

        Payment.objects.create(
            order=self.other_order,
            payment_method='card',
            amount=self.other_order.total_amount
        )

        response = self.client.get(self.payment_history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        payments = response.data.get('results', response.data)

        self.assertEqual(len(payments), 1)

    # 10. Reject invalid payment verification result
    def test_invalid_payment_verification_result(self):

        payment = Payment.objects.create(
            order=self.order,
            payment_method='upi',
            amount=self.order.total_amount
        )

        response = self.client.post(
            reverse('verify-payment', kwargs={'pk': payment.pk}),
            {'result': 'invalid'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        payment.refresh_from_db()

        self.assertEqual(payment.payment_status, 'pending')

class ProductReviewAPITestCase(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username='reviewuser',
            email='reviewuser@example.com',
            password='Test@12345'
        )

        self.other_user = User.objects.create_user(
            username='otherreviewuser',
            email='otherreviewuser@example.com',
            password='Test@12345'
        )

        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            slug='laptop',
            description='Test Laptop',
            price=Decimal('2500.00'),
            discount_price=Decimal('1999.00'),
            stock_quantity=10,
            is_active=True
        )

        self.review_list_url = reverse('product-reviews')

        self.client.force_authenticate(user=self.user)

    def create_delivered_order(self):

        order = Order.objects.create(
            user=self.user,
            shipping_address='Trivandrum, Kerala, India',
            total_amount=Decimal('1999.00'),
            status='delivered'
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=Decimal('1999.00'),
            quantity=1
        )

        return order

    def create_review(self, user=None):

        return ProductReview.objects.create(
            product=self.product,
            user=user or self.user,
            rating=5,
            comment='Excellent product!'
        )

    # 1. Public users can view reviews
    def test_list_reviews_publicly(self):

        self.create_review()

        self.client.force_authenticate(user=None)

        response = self.client.get(self.review_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # 2. Filter reviews by product
    def test_filter_reviews_by_product(self):

        self.create_review()

        response = self.client.get(
            self.review_list_url,
            {'product': self.product.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        reviews = response.data.get('results', response.data)

        self.assertEqual(len(reviews), 1)

    # 3. Create review after delivered order
    def test_create_review_after_delivery(self):

        self.create_delivered_order()

        response = self.client.post(
            self.review_list_url,
            {
                'product': self.product.id,
                'rating': 5,
                'comment': 'Excellent product!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductReview.objects.count(), 1)

    # 4. Prevent review without delivered order
    def test_prevent_review_without_delivery(self):

        response = self.client.post(
            self.review_list_url,
            {
                'product': self.product.id,
                'rating': 4,
                'comment': 'Good product'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ProductReview.objects.count(), 0)

    # 5. Prevent duplicate review for same product
    def test_prevent_duplicate_review(self):

        self.create_delivered_order()
        self.create_review()

        response = self.client.post(
            self.review_list_url,
            {
                'product': self.product.id,
                'rating': 4,
                'comment': 'Another review'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ProductReview.objects.count(), 1)

    # 6. Prevent unauthenticated review creation
    def test_unauthenticated_user_cannot_create_review(self):

        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.review_list_url,
            {
                'product': self.product.id,
                'rating': 5,
                'comment': 'Excellent'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 7. Retrieve own review
    def test_retrieve_own_review(self):

        review = self.create_review()

        response = self.client.get(
            reverse(
                'product-review-detail',
                kwargs={'pk': review.pk}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # 8. Prevent access to another user's review
    def test_cannot_access_other_users_review(self):

        review = self.create_review(user=self.other_user)

        response = self.client.get(
            reverse(
                'product-review-detail',
                kwargs={'pk': review.pk}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 9. Update own review
    def test_update_own_review(self):

        review = self.create_review()

        response = self.client.patch(
            reverse(
                'product-review-detail',
                kwargs={'pk': review.pk}
            ),
            {
                'rating': 4,
                'comment': 'Updated review'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        review.refresh_from_db()

        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Updated review')

    # 10. Delete own review
    def test_delete_own_review(self):

        review = self.create_review()

        response = self.client.delete(
            reverse(
                'product-review-detail',
                kwargs={'pk': review.pk}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ProductReview.objects.filter(pk=review.pk).exists()
        )

class NotificationAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='notification_user',
            email='notification_user@test.com',
            password='test123'
        )

        self.other_user = User.objects.create_user(
            username='other_notification_user',
            email='other_notification_user@test.com',
            password='test123'
        )

        self.notification = Notification.objects.create(
            user=self.user,
            title='Order Update',
            message='Your order has been confirmed.',
            notification_type='order'
        )

        self.url = reverse('notification-list')

    def test_authenticated_user_can_list_notifications(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(len(response.data['results']), 1)
    def test_user_can_only_see_own_notifications(self):
        Notification.objects.create(
            user=self.other_user,
            title='Payment Update',
            message='Payment successful.',
            notification_type='payment'
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(len(response.data['results']), 1)

    def test_unauthenticated_user_cannot_list_notifications(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_user_can_mark_notification_as_read(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            'notification-read',
            kwargs={'pk': self.notification.id}
        )

        response = self.client.patch(
            url,
            {'is_read': True},
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_user_cannot_update_another_users_notification(self):
        self.client.force_authenticate(user=self.other_user)

        url = reverse(
            'notification-read',
            kwargs={'pk': self.notification.id}
        )

        response = self.client.patch(
            url,
            {'is_read': True},
            format='json'
        )

        self.assertEqual(response.status_code, 404)

    def test_notification_content_is_read_only(self):
        self.client.force_authenticate(user=self.user)

        url = reverse(
            'notification-read',
            kwargs={'pk': self.notification.id}
        )

        response = self.client.patch(
            url,
            {
                'title': 'Changed title',
                'is_read': True
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)

        self.notification.refresh_from_db()
        self.assertEqual(self.notification.title, 'Order Update')

class DashboardAPITestCase(APITestCase):

    def setUp(self):

        self.admin_user = User.objects.create_user(
            username='dashboard_admin',
            email='dashboard_admin@test.com',
            password='test123',
            is_staff=True
        )

        self.normal_user = User.objects.create_user(
            username='dashboard_customer',
            email='dashboard_customer@test.com',
            password='test123'
        )

        self.category = Category.objects.create(
            name='Dashboard Electronics',
            slug='dashboard-electronics'
        )

        self.product = Product.objects.create(
            category=self.category,
            name='Dashboard Laptop',
            slug='dashboard-laptop',
            price=Decimal('50000.00'),
            stock_quantity=10
        )

        self.order = Order.objects.create(
            user=self.normal_user,
            shipping_address='Trivandrum, Kerala, India',
            total_amount=Decimal('50000.00'),
            status='pending'
        )

        self.payment = Payment.objects.create(
            order=self.order,
            payment_method='upi',
            payment_status='successful',
            amount=Decimal('50000.00')
        )

        self.url = reverse('dashboard')

    def test_admin_can_access_dashboard(self):

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_normal_user_cannot_access_dashboard(self):

        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cannot_access_dashboard(self):

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_dashboard_returns_correct_statistics(self):

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['total_customers'], 1)
        self.assertEqual(response.data['total_products'], 1)
        self.assertEqual(response.data['total_categories'], 1)
        self.assertEqual(response.data['total_orders'], 1)
        self.assertEqual(response.data['pending_orders'], 1)
        self.assertEqual(
            Decimal(str(response.data['total_revenue'])),
            Decimal('50000.00')
        )
