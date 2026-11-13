from rest_framework import serializers
from .models import Product,StockMovement,Category,Cart,CartItem,Order,OrderItem,Payment,ProductReview,Notification
from decimal import Decimal



class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'category',
            'category_name',
            'name',
            'slug',
            'description',
            'price',
            'discount_price',
            'image',
            'stock_quantity',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than zero."
            )
        return value

    def validate(self, attrs):
        price = attrs.get(
            'price',
            self.instance.price if self.instance else None
        )

        discount_price = attrs.get(
            'discount_price',
            self.instance.discount_price if self.instance else None
        )

        if discount_price is not None:
            if discount_price < 0:
                raise serializers.ValidationError({
                    'discount_price': 'Discount price cannot be negative.'
                })

            if price is not None and discount_price >= price:
                raise serializers.ValidationError({
                    'discount_price': 'Discount price must be less than the regular price.'
                })

        return attrs


class StockUpdateSerializer(serializers.Serializer):
    stock_quantity = serializers.IntegerField(min_value=0)

class StockAdjustmentSerializers(serializers.Serializer):

    adjustment_type=serializers.ChoiceField(
        choices=['add','remove']
    )

    quantity=serializers.IntegerField(min_value=1)

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )
    class Meta:
        model = StockMovement
        fields = [
            'id',
            'product',
            'product_name',
            'adjustment_type',
            'quantity',
            'previous_stock',
            'current_stock',
            'adjusted_by',
            'created_at'
        ]

        read_only_fields = fields
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'image',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        source='product'
    )

    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        product = attrs['product']
        quantity = attrs['quantity']

        if quantity > product.stock_quantity:
            raise serializers.ValidationError({
                'quantity': 'Requested quantity exceeds available stock.'
            })

        return attrs


class CartItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    unit_price = serializers.SerializerMethodField()

    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_name',
            'unit_price',
            'quantity',
            'subtotal',
            'created_at',
            'updated_at'
        ]

        read_only_fields = fields

    def get_unit_price(self, obj):
        return obj.product.discount_price or obj.product.price

    def get_subtotal(self, obj):
        price = self.get_unit_price(obj)
        return price * obj.quantity


class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(many=True, read_only=True)

    total_items = serializers.SerializerMethodField()

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'items',
            'total_items',
            'total_price',
            'created_at',
            'updated_at'
        ]

        read_only_fields = fields

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        total = Decimal('0.00')

        for item in obj.items.select_related('product').all():
            price = item.product.discount_price or item.product.price
            total += price * item.quantity

        return total

class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class PlaceOrderSerializer(serializers.Serializer):

    shipping_address = serializers.CharField(
        max_length=1000,
        min_length=10
    )


class OrderItemSerializer(serializers.ModelSerializer):

    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'unit_price',
            'quantity',
            'subtotal',
            'created_at'
        ]

        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'shipping_address',
            'items',
            'total_amount',
            'status',
            'created_at',
            'updated_at'
        ]

        read_only_fields = fields

class UpdateOrderStatusSerializer(serializers.Serializer):

    status = serializers.ChoiceField(
        choices=[
            'confirmed',
            'processing',
            'shipped',
            'delivered'
        ]
    )

class PaymentSerializer(serializers.ModelSerializer):

    order_number = serializers.UUIDField(
        source='order.order_number',
        read_only=True
    )

    class Meta:
        model = Payment

        fields = [
            'id',
            'payment_reference',
            'order',
            'order_number',
            'payment_method',
            'payment_status',
            'amount',
            'transaction_id',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'payment_reference',
            'payment_status',
            'amount',
            'transaction_id',
            'created_at',
            'updated_at'
        ]

class CreatePaymentSerializer(serializers.Serializer):

    order = serializers.IntegerField()

    payment_method = serializers.ChoiceField(
        choices=[
            'upi',
            'card',
            'net_banking',
            'cash_on_delivery'
        ]
    )

class PaymentVerificationSerializer(serializers.Serializer):

    result = serializers.ChoiceField(
        choices=[
            'success',
            'failure'
        ]
    )

class ProductReviewSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = ProductReview

        fields = [
            'id',
            'product',
            'product_name',
            'user',
            'username',
            'rating',
            'comment',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'user',
            'username',
            'created_at',
            'updated_at'
        ]

class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification

        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'is_read',
            'created_at'
        ]

        read_only_fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'created_at'
        ]
