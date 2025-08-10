from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.blog_landing, name="blog_landing"),
    path("posts/", views.BlogListView.as_view(), name="blog_list"),
    path("post/<slug:slug>/", views.BlogDetailView.as_view(), name="post_detail"),
    path("create/", views.BlogCreateView.as_view(), name="post_create"),
    path("edit/<slug:slug>/", views.BlogUpdateView.as_view(), name="post_edit"),
    path("delete/<slug:slug>/", views.BlogDeleteView.as_view(), name="post_delete"),
    path("dashboard/", views.blog_dashboard, name="dashboard"),
    path("upload-image/", views.upload_image, name="upload_image"),
    path("feed/", views.BlogRSSFeed(), name="rss_feed"),
]
