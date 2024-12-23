import csv

import pandas as pd
from rest_framework import status, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Favorite, User
from .serializers import UserSerializer
from .utils import send_otp
from rest_framework_simplejwt.tokens import RefreshToken
import pickle
from django.conf import settings
from rest_framework import status
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
import jwt

@api_view(['POST'])
@permission_classes([AllowAny]) 
def signup(request):
    print(f"Received request data: {request.data}")
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        try:
            otp = send_otp(user.email) 
            user.otp = otp
            user.save()
            return Response({"message": "User created, OTP sent"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            user.delete()  
            print(f"OTP sending failed: {str(e)}")
            return Response({"error": "Error sending OTP, please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        print(f"Validation Errors: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny]) 
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")
    try:
        user = User.objects.get(email=email)
        if user.otp == otp:
            user.is_verified = True
            user.save()
            return Response({"message": "Account verified!"}, status=status.HTTP_200_OK)
        return Response({"message": "Invalid OTP!"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"message": "User not found!"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny]) 
def signin(request):
    email = request.data.get("email")
    password = request.data.get("password")
    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            if not user.is_verified:
                return Response({"message": "Account not verified!"}, status=status.HTTP_400_BAD_REQUEST)
            refresh = RefreshToken.for_user(user)
            return Response({"access_token": str(refresh.access_token)}, status=status.HTTP_200_OK)
        return Response({"message": "Invalid credentials!"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"message": "User not found!"}, status=status.HTTP_400_BAD_REQUEST)


movies = pickle.load(open("authentication/movies_list.pkl", 'rb'))
similarity = pickle.load(open("authentication/similarity.pkl", 'rb'))

def fetch_poster(movie_id):

    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=601cc60dc1a6b8d9faa9e225312eb719&language=en-US"
        data = requests.get(url).json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500/{poster_path}"
        return None
    except Exception:
        return None 
    
@api_view(['GET'])
@permission_classes([AllowAny]) 
def home(request):
    try:
        pkl_file_path = 'authentication/movies_first_500.pkl'

        with open(pkl_file_path, 'rb') as file:
            df = pickle.load(file)

    

        df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0)

    
        filtered_movies = df[df['vote_average'] >= 8.5]

     
        movies = []
        for _, row in filtered_movies.iterrows():
            poster = fetch_poster(row.get("id"))
            movie_details = {
                "id": row.get("id"),
                "title": row.get("title"),
                "poster": poster,
                "overview": row.get("overview"),
                "genre": row.get("genre"),
                "release_date": row.get("release_date"),
                "vote_average": row.get("vote_average"),
            }
            print('movieDetails',movie_details)
            movies.append(movie_details)

        return Response({"movies": movies}, status=status.HTTP_200_OK)

    except FileNotFoundError:
        return Response(
            {"error": "Movies file not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    


@api_view(['GET'])
@permission_classes([AllowAny]) 
def filter(request):
    try:
        genre_filter = request.query_params.get('genre', None)
        vote_average_filter = request.query_params.get('vote_average', None)

        if vote_average_filter:
            try:
                vote_average_filter = float(vote_average_filter)
            except ValueError:
                return Response({"error": "Invalid vote_average value."}, status=status.HTTP_400_BAD_REQUEST)

        pkl_file_path = 'authentication/movies_first_500.pkl'  
       
        try:
            with open(pkl_file_path, 'rb') as file:
                df = pickle.load(file)
        except FileNotFoundError:
            return Response({"error": "Movies file not found."}, status=status.HTTP_404_NOT_FOUND)

        df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0)

        
        if vote_average_filter is not None:
            df = df[df["vote_average"] >= vote_average_filter]

       
        if genre_filter:
            df = df[df["genre"].str.contains(genre_filter, case=False, na=False)]

        
        movies = []
        for _, row in df.iterrows():
            poster = fetch_poster(row.get("id"))
            movies.append({
                "id": row.get("id"),
                "title": row.get("title"),
                "poster": poster,
                "overview": row.get("overview"),
                "genre": row.get("genre"),
                "release_date": row.get("release_date"),
                "vote_average": row.get("vote_average"),
            })
 
        return Response({"movies": movies}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )




    
@api_view(['POST'])
@permission_classes([AllowAny]) 
def recommend_movies(request):
    
    movie_name = request.data.get('movie_name')
    
    if not movie_name:
        return Response({"error": "Movie name is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
       
        index = movies[movies['title'] == movie_name].index[0]
        
        
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])
        
        
        recommended_movies = []
        for i in distances[1:6]:
            movie_id = movies.iloc[i[0]].id
            title = movies.iloc[i[0]].title
            poster = fetch_poster(movie_id)
            recommended_movies.append({"id": movie_id , "title": title, "poster_url": poster})
        
        return Response({"recommendations": recommended_movies}, status=status.HTTP_200_OK)
    
    except IndexError:
        return Response({"error": "Movie not found in database"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([AllowAny]) 
def get_movie_details(request, id):
    try:
        pkl_file_path = 'authentication/movies_list.pkl'

        with open(pkl_file_path, 'rb') as file:
            df = pickle.load(file)

        movie = df[df['id'] == id].iloc[0]
        id = movie.id
        print("id", movie.id)

        movie_details = {
            "id": movie.get("id"),
            "title": movie.get("title"),
            "poster": fetch_poster(id),
            "overview": movie.get("overview"),
            "genre": movie.get("genre"),
            "release_date": movie.get("release_date"),
            "vote_average": movie.get("vote_average"),
        }

        return Response(movie_details, status=status.HTTP_200_OK)

    except IndexError:
        return Response({"error": "Movie not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny]) 
def search_movies(request):
    try:
        query = request.query_params.get('q', '').lower()
        if not query:
            return Response({"suggestions": []}, status=status.HTTP_200_OK)

        pkl_file_path = 'authentication/movies_list.pkl'
        with open(pkl_file_path, 'rb') as file:
            df = pickle.load(file)

     
        suggestions = df[df['title'].str.lower().str.contains(query, na=False)].head(10)

        
        suggestions_list = [{"id": row['id'], "title": row['title']} for _, row in suggestions.iterrows()]
        return Response({"suggestions": suggestions_list}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_favorites(request):
   
    user = request.user




    movie_id = request.data.get('movie_id')
    title = request.data.get('title')
    poster_url = request.data.get('poster_url')
    overview = request.data.get('overview')
    genre = request.data.get('genre')
    release_date = request.data.get('release_date')
    vote_average = request.data.get('vote_average')

    if not all([movie_id, title, poster_url, overview, genre, release_date, vote_average]):
        return Response({"error": "All movie details are required!"}, status=status.HTTP_400_BAD_REQUEST)

    
    if Favorite.objects.filter(user=user, movie_id=movie_id).exists():
        return Response({"message": "Movie is already in your favorites!"}, status=status.HTTP_400_BAD_REQUEST)

    favorite = Favorite.objects.create(
        user=user,
        movie_id=movie_id,
        title=title,
        poster_url=poster_url,
        overview=overview,
        genre=genre,
        release_date=release_date,
        vote_average=vote_average,
    )

    return Response({"message": "Movie added to favorites!"}, status=status.HTTP_201_CREATED)


def create_jwt_token(user):
    refresh = RefreshToken.for_user(user)

    access_token = refresh.access_token
    access_token['user_id'] = user.id  
    return str(access_token)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_from_favorites(request):
    user = request.user
    movie_id = request.data.get('movie_id')

    if not movie_id:
        return Response({"error": "Movie ID is required!"}, status=status.HTTP_400_BAD_REQUEST)

    try:
    
        favorite = Favorite.objects.get(user=user, movie_id=movie_id)
        favorite.delete()
        return Response({"message": "Movie removed from favorites!"}, status=status.HTTP_200_OK)
    except Favorite.DoesNotExist:
        return Response({"error": "Movie not found in your favorites!"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorites(request):
    user = request.user

    
    favorites = Favorite.objects.filter(user=user)
    
    
    favorite_movies = [
        {
            "movie_id": favorite.movie_id,
            "title": favorite.title,
            "poster_url": favorite.poster_url,
            "overview": favorite.overview,
            "genre": favorite.genre,
            "release_date": favorite.release_date,
            "vote_average": favorite.vote_average,
        }
        for favorite in favorites
    ]

    return Response({"favorites": favorite_movies}, status=status.HTTP_200_OK)
