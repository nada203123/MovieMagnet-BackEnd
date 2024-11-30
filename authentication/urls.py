from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('signup/', views.signup),
    path('verify-otp/', views.verify_otp),
    path('signin/', views.signin),
    path('home/', views.home),
    path('filter/', views.filter),
    path('recommend/',views.recommend_movies,name='recommend_movies'),
    path('movie/<int:id>/', views.get_movie_details, name='get_movie_details'),
    path('search/', views.search_movies),
    path('addfavorite/', views.add_to_favorites, name='add_to_favorites'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('delete/', views.delete_from_favorites, name='delete_from_favorites'),
    path('favorites/', views.get_favorites, name='get_favorites'),
]