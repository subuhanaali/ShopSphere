from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from django.db import transaction
from .serializers import StockAdjustmentSerializers,CategorySerializer,PlaceOrderSerializer,OrderSerializer,CreatePaymentSerializer,PaymentSerializer,PaymentVerificationSerializer,ProductReviewSerializer,DashboardSerializer
from .models import Product,StockMovement,Category,Cart, CartItem,Order,OrderItem,Payment,ProductReview,Notification
from .serializers import ProductSerializer, StockUpdateSerializer,StockMovementSerializer,CategorySerializer,CartSerializer,CartItemSerializer,UpdateCartItemSerializer,AddToCartSerializer,UpdateOrderStatusSerializer,NotificationSerializer
from .permissions import IsAdminUserOrReadOnly
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from decimal import Decimal
import uuid
from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    # Product filtering
    filterset_fields = ['category', 'price']

    # Product search
    search_fields = ['name', 'description']

    # Product sorting
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUserOrReadOnly]

class ProductStockUpdateView(APIView):
    serializer_class = StockUpdateSerializer
    permission_classes=[IsAdminUser]
    @extend_schema(request=StockUpdateSerializer)
    
    def patch(self, request, pk):

        serializer = StockUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data['stock_quantity']

        if quantity is None:
            return Response(
                {'error': 'stock_quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if quantity < 0:
            return Response(
                {'error': 'Stock cannot be negative'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():

            try:
                product = Product.objects.select_for_update().get(pk=pk)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            product.stock_quantity = quantity
            product.save(update_fields=['stock_quantity'])

        return Response({
            'message': 'Stock updated successfully',
            'product': product.name,
            'stock_quantity': product.stock_quantity
        }, status=status.HTTP_200_OK)

class LowStockProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]

    queryset = Product.objects.filter(
        stock_quantity__lt=5,
        is_active=True
    ).order_by('stock_quantity')

class ProductStockAdjustmentView(APIView):
    serializer_class = StockAdjustmentSerializers
    permission_classes=[IsAdminUser]

    @extend_schema(request=StockAdjustmentSerializers)
    def patch(self,request,pk):
        serializer=StockAdjustmentSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        adjustment_type=serializer.validated_data['adjustment_type']
        quantity=serializer.validated_data['quantity']
        with transaction.atomic():

            try:
                product = Product.objects.select_for_update().get(pk=pk)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            current_stock = product.stock_quantity

            if adjustment_type == 'add':
                new_stock = current_stock + quantity

            else:
                if quantity > current_stock:
                    return Response(
                        {'error': 'Insufficient stock available'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                new_stock = current_stock - quantity

            product.stock_quantity = new_stock
            product.save(update_fields=['stock_quantity'])

            StockMovement.objects.create(
                product=product,
                adjustment_type=adjustment_type,
                quantity=quantity,
                previous_stock=current_stock,
                current_stock=new_stock,
                adjusted_by=request.user
)

        return Response({
            'message': 'Stock adjusted successfully',
            'product': product.name,
            'adjustment_type': adjustment_type,
            'adjusted_quantity': quantity,
            'previous_stock': current_stock,
            'current_stock': new_stock
        }, status=status.HTTP_200_OK)
class StockMovementListView(generics.ListAPIView):

    queryset = StockMovement.objects.select_related(
        'product',
        'adjusted_by'
    ).all()

    serializer_class = StockMovementSerializer
    permission_classes = [IsAdminUser]
class CategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('name')

class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {
                    "detail": "Cannot delete this category because products are associated with it."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

class AddToCartView(APIView):
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(request=AddToCartSerializer)
    def post(self, request):

        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        with transaction.atomic():

            product = Product.objects.select_for_update().get(
                pk=product.pk
            )

            if not product.is_active:
                if quantity > product.stock_quantity:
                    return Response(
                        {'error': 'Requested quantity exceeds available stock.'},
                        status=status.HTTP_400_BAD_REQUEST
    )
                return Response(
                    {'error': 'Product is not available.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart, _ = Cart.objects.get_or_create(
                user=request.user
            )

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                new_quantity = cart_item.quantity + quantity

                if new_quantity > product.stock_quantity:
                    return Response(
                        {'error': 'Requested quantity exceeds available stock.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                cart_item.quantity = new_quantity
                cart_item.save(update_fields=['quantity', 'updated_at'])

        return Response(
            {
                'message': 'Product added to cart successfully.',
                'cart': CartSerializer(cart).data
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class CartDetailView(APIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    

    def get(self, request):

        cart, _ = Cart.objects.get_or_create(
            user=request.user
        )

        serializer = CartSerializer(cart)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class UpdateCartItemView(APIView):
    serializer_class = UpdateCartItemSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(request=UpdateCartItemSerializer)
    def patch(self, request, pk):

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data['quantity']

        with transaction.atomic():

            cart_item = get_object_or_404(
                CartItem.objects.select_for_update().select_related('product'),
                pk=pk,
                cart__user=request.user
            )

            product = Product.objects.select_for_update().get(
                pk=cart_item.product_id
            )

            if not product.is_active:
                return Response(
                    {'error': 'Product is not available.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if quantity > product.stock_quantity:
                return Response(
                    {'error': 'Requested quantity exceeds available stock.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cart_item.quantity = quantity
            cart_item.save(update_fields=['quantity', 'updated_at'])

        return Response(
            {
                'message': 'Cart quantity updated successfully.',
                'cart_item': CartItemSerializer(cart_item).data
            },
            status=status.HTTP_200_OK
        )
    def delete(self, request, pk):

        with transaction.atomic():

            cart_item = get_object_or_404(
                CartItem.objects.select_for_update(),
                pk=pk,
                cart__user=request.user
            )

            cart_item.delete()

        return Response(
            {'message': 'Cart item removed successfully.'},
            status=status.HTTP_200_OK
        )
class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PlaceOrderSerializer,
        responses={201: OrderSerializer}
    )
    def post(self, request):

        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shipping_address = serializer.validated_data['shipping_address']

        with transaction.atomic():

            # Get and lock the user's cart
            try:
                cart = Cart.objects.select_for_update().get(
                    user=request.user
                )
            except Cart.DoesNotExist:
                return Response(
                    {'error': 'Your cart is empty.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get cart items
            cart_items = list(
                CartItem.objects.select_for_update()
                .filter(cart=cart)
                .order_by('product_id')
            )

            if not cart_items:
                return Response(
                    {'error': 'Your cart is empty.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Lock all products in a consistent order
            product_ids = [item.product_id for item in cart_items]

            products = Product.objects.select_for_update().filter(
                id__in=product_ids
            ).order_by('id')

            product_map = {
                product.id: product for product in products
            }

            # Validate products and stock before creating the order
            total_amount = Decimal('0.00')

            for item in cart_items:

                product = product_map.get(item.product_id)

                if product is None or not product.is_active:
                    return Response(
                        {
                            'error': (
                                f'Product {item.product_id} is no longer available.'
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if item.quantity > product.stock_quantity:
                    return Response(
                        {
                            'error': (
                                f'Insufficient stock for {product.name}. '
                                f'Available stock: {product.stock_quantity}.'
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                unit_price = (
                    product.discount_price
                    if product.discount_price is not None
                    else product.price
                )

                total_amount += unit_price * item.quantity

            # Create the order
            order = Order.objects.create(
                user=request.user,
                shipping_address=shipping_address,
                total_amount=total_amount,
                status='pending'
            )

            # Create order items and deduct stock
            for item in cart_items:

                product = product_map[item.product_id]

                unit_price = (
                    product.discount_price
                    if product.discount_price is not None
                    else product.price
                )

                previous_stock = product.stock_quantity
                current_stock = previous_stock - item.quantity

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    unit_price=unit_price,
                    quantity=item.quantity
                )

                product.stock_quantity = current_stock
                product.save(update_fields=['stock_quantity'])

                # Record stock movement
                StockMovement.objects.create(
                    product=product,
                    adjustment_type='remove',
                    quantity=item.quantity,
                    previous_stock=previous_stock,
                    current_stock=current_stock,
                    adjusted_by=request.user
                )

            # Clear cart after successful order creation
            CartItem.objects.filter(cart=cart).delete()

        return Response(
            {
                'message': 'Order placed successfully.',
                'order': OrderSerializer(order).data
            },
            status=status.HTTP_201_CREATED
        )


# Get all orders of the logged-in user
class OrderListView(generics.ListAPIView):

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()

        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items')


# Get details of a specific order
class OrderDetailView(generics.RetrieveAPIView):

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items')

class CancelOrderView(APIView):
    serializer_class = OrderSerializer

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        with transaction.atomic():

            # Get and lock the order belonging to the logged-in user
            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=pk,
                user=request.user
            )

            # Check whether the order can be cancelled
            if order.status == 'cancelled':
                return Response(
                    {'error': 'This order has already been cancelled.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if order.status not in ['pending', 'confirmed', 'processing']:
                return Response(
                    {'error': 'This order cannot be cancelled.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get all order items
            order_items = list(
                OrderItem.objects.filter(
                    order=order
                ).order_by('product_id')
            )

            # Lock products
            product_ids = [item.product_id for item in order_items]

            products = Product.objects.select_for_update().filter(
                id__in=product_ids
            ).order_by('id')

            product_map = {
                product.id: product for product in products
            }

            # Restore stock for each product
            for item in order_items:

                product = product_map[item.product_id]

                previous_stock = product.stock_quantity
                current_stock = previous_stock + item.quantity

                product.stock_quantity = current_stock
                product.save(update_fields=['stock_quantity'])

                # Record stock restoration
                StockMovement.objects.create(
                    product=product,
                    adjustment_type='add',
                    quantity=item.quantity,
                    previous_stock=previous_stock,
                    current_stock=current_stock,
                    adjusted_by=request.user
                )

            # Update order status
            # Mark successful payments as refunded
            Payment.objects.filter(
                order=order,
                payment_status='successful'
            ).update(
                payment_status='refunded'
            )

            # Update order status
            order.status = 'cancelled'
            order.save(update_fields=['status', 'updated_at'])

        return Response(
            {
                'message': 'Order cancelled successfully.',
                'order': OrderSerializer(order).data
            },
            status=status.HTTP_200_OK
        )

class UpdateOrderStatusView(APIView):
    serializer_class = UpdateOrderStatusSerializer

    permission_classes = [IsAdminUser]

    @extend_schema(request=UpdateOrderStatusSerializer)
    def patch(self, request, pk):

        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']

        allowed_transitions = {
            'pending': 'confirmed',
            'confirmed': 'processing',
            'processing': 'shipped',
            'shipped': 'delivered'
        }

        with transaction.atomic():

            order = get_object_or_404(
                Order.objects.select_for_update(),
                pk=pk
            )

            expected_status = allowed_transitions.get(order.status)

            if expected_status is None:
                return Response(
                    {
                        'error': 'This order cannot be updated.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_status != expected_status:
                return Response(
                    {
                        'error': (
                            f'Invalid status transition. '
                            f'Next allowed status is {expected_status}.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])

        return Response(
            {
                'message': 'Order status updated successfully.',
                'order': OrderSerializer(order).data
            },
            status=status.HTTP_200_OK
        )

class CreatePaymentView(APIView):
    serializer_class = CreatePaymentSerializer

    permission_classes = [IsAuthenticated]

    @extend_schema(request=CreatePaymentSerializer)
    
    def post(self, request):

        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data['order']
        payment_method = serializer.validated_data['payment_method']

        with transaction.atomic():

            # Lock the order belonging to the logged-in user
            order = get_object_or_404(
                Order.objects.select_for_update(),
                id=order_id,
                user=request.user
            )

            # Validate order status
            if order.status not in ['pending', 'confirmed']:
                return Response(
                    {'error': 'Payment is not allowed for this order.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check for an existing successful payment
            if Payment.objects.filter(
                order=order,
                payment_status='successful'
            ).exists():
                return Response(
                    {'error': 'This order has already been paid.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prevent multiple pending payment attempts
            if Payment.objects.filter(
                order=order,
                payment_status='pending'
            ).exists():
                return Response(
                    {'error': 'A payment is already pending for this order.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            payment = Payment.objects.create(
                order=order,
                payment_method=payment_method,
                amount=order.total_amount,
                payment_status='pending'
            )

        return Response(
            {
                'message': 'Payment initiated successfully.',
                'payment': PaymentSerializer(payment).data
            },
            status=status.HTTP_201_CREATED
        )


class VerifyPaymentView(APIView):
    serializer_class = PaymentVerificationSerializer

    permission_classes = [IsAuthenticated]

    @extend_schema(request=PaymentVerificationSerializer)
    def post(self, request, pk):

        serializer = PaymentVerificationSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.validated_data['result']

        with transaction.atomic():

            payment = get_object_or_404(
                Payment.objects.select_for_update().select_related('order'),
                pk=pk,
                order__user=request.user
            )

            if payment.payment_status != 'pending':
                return Response(
                    {
                        'error': 'This payment has already been processed.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if result == 'success':

                payment.payment_status = 'successful'
                payment.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

                payment.order.status = 'confirmed'
                payment.order.save(
                    update_fields=['status', 'updated_at']
                )

            else:

                payment.payment_status = 'failed'

            payment.save(
                update_fields=[
                    'payment_status',
                    'transaction_id',
                    'updated_at'
                ]
            )

        return Response(
            {
                'message': 'Payment verification completed.',
                'payment': PaymentSerializer(payment).data
            },
            status=status.HTTP_200_OK
        )

class PaymentHistoryView(generics.ListAPIView):

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Payment.objects.none()

        return Payment.objects.filter(
            order__user=self.request.user
         ).select_related('order')

class ProductReviewListCreateView(generics.ListCreateAPIView):

    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = ProductReview.objects.select_related(
            'product', 'user'
        )

        product_id = self.request.query_params.get('product')

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    def perform_create(self, serializer):

        product = serializer.validated_data['product']

        # Check whether the customer has purchased and received the product
        has_purchased = OrderItem.objects.filter(
            product=product,
            order__user=self.request.user,
            order__status='delivered'
        ).exists()

        if not has_purchased:
            raise ValidationError(
                "You can review a product only after purchasing and receiving it."
            )

        # Prevent duplicate reviews
        already_reviewed = ProductReview.objects.filter(
            product=product,
            user=self.request.user
        ).exists()

        if already_reviewed:
            raise ValidationError(
                "You have already reviewed this product."
            )

        serializer.save(user=self.request.user)

class ProductReviewDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProductReview.objects.filter(
            user=self.request.user
        )

class NotificationListView(generics.ListAPIView):

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()

        return Notification.objects.filter(
            user=self.request.user
        )


class MarkNotificationReadView(generics.UpdateAPIView):

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        )

class DashboardView(APIView):
    serializer_class = DashboardSerializer

    permission_classes = [IsAdminUser]

    def get(self, request):

        User = get_user_model()

        total_customers = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).count()

        total_products = Product.objects.count()

        total_categories = Category.objects.count()

        total_orders = Order.objects.count()

        pending_orders = Order.objects.filter(
            status='pending'
        ).count()

        total_revenue = Payment.objects.filter(
            payment_status='successful'
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        return Response(
            {
                'total_customers': total_customers,
                'total_products': total_products,
                'total_categories': total_categories,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'total_revenue': total_revenue
            },
            status=status.HTTP_200_OK
        )
