from django.urls import path
from .views import ProductListCreateView,ProductDetailView,ProductStockUpdateView,LowStockProductsView,ProductStockAdjustmentView,StockMovementListView,CategoryListCreateAPIView,CategoryDetailAPIView,AddToCartView,CartDetailView,UpdateCartItemView,PlaceOrderView,OrderListView,OrderDetailView,CancelOrderView,UpdateOrderStatusView,CreatePaymentView,VerifyPaymentView,PaymentHistoryView,ProductReviewListCreateView
from .views import ProductReviewDetailView,MarkNotificationReadView,NotificationListView,DashboardView
urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/update-stock/',ProductStockUpdateView.as_view(),name='product-stock-update'),
    path('low-stock/',LowStockProductsView.as_view(),name='low-stock-products'),
    path('<int:pk>/adjust-stock/',ProductStockAdjustmentView.as_view()),
    path('stock-movements/',StockMovementListView.as_view(),name='stock-movements'),
    path('categories/',CategoryListCreateAPIView.as_view(),name='category-list-create'),
    path('categories/<int:pk>/',CategoryDetailAPIView.as_view(),name='category-detail'),
    # Shopping Cart APIs
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/items/<int:pk>/',UpdateCartItemView.as_view(),name='cart-item-detail'),
    path('orders/place/',PlaceOrderView.as_view(),name='place-order'),
    # Order APIs
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/cancel/', CancelOrderView.as_view(),name='cancel-order'),
    path('orders/<int:pk>/status/',UpdateOrderStatusView.as_view(),name='update-order-status'),
    path('payments/create/',CreatePaymentView.as_view(),name='create-payment'),
    path('payments/<int:pk>/verify/',VerifyPaymentView.as_view(),name='verify-payment'),
    path('payments/history/',PaymentHistoryView.as_view(),name='payment-history'),
    path('reviews/',ProductReviewListCreateView.as_view(),name='product-reviews'),
    path(
    'reviews/<int:pk>/',
    ProductReviewDetailView.as_view(),
    name='product-review-detail'
),

path(
    'notifications/',
    NotificationListView.as_view(),
    name='notification-list'
),
path(
    'notifications/<int:pk>/',
    MarkNotificationReadView.as_view(),
    name='notification-read'
),
path(
    'dashboard/',
    DashboardView.as_view(),
    name='dashboard'
),
]