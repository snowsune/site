from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.BlogListView.as_view(), name="blog_list"),
    path("post/<slug:slug>/", views.BlogDetailView.as_view(), name="post_detail"),
    path("create/", views.BlogCreateView.as_view(), name="post_create"),
    path("edit/<slug:slug>/", views.BlogUpdateView.as_view(), name="post_edit"),
    path("delete/<slug:slug>/", views.BlogDeleteView.as_view(), name="post_delete"),
    path("dashboard/", views.blog_dashboard, name="dashboard"),
    path("upload-image/", views.upload_image, name="upload_image"),
    path("feed/", views.BlogRSSFeed(), name="rss_feed"),
    # Comment functionality
    path("post/<int:post_id>/comment/", views.submit_comment, name="submit_comment"),
    path(
        "comment/<int:comment_id>/<str:action>/",
        views.moderate_comment,
        name="moderate_comment",
    ),
]
