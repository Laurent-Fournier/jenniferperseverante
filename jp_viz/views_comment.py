from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse

from django_ratelimit.decorators import ratelimit

from .models import Comment


# ------------------
# Add comment
# ------------------
@ratelimit(key="ip", rate="3/m", method="POST", block=True)
def add_comment(request, lg):
    if request.method == "POST":
        article_id = request.POST.get("art_id")
        article_slug = request.POST.get("art_slug")
        parent_id = request.POST.get("parent_id")
        author = request.POST.get("author")
        email = request.POST.get("email")
        content = request.POST.get("content")

        if parent_id == "":
            parent_id = None

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR")

        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Comment creation
        comment = Comment.objects.create(
            art_id=article_id,
            language_code=lg,
            com_parent_id=parent_id,
            com_author=author,
            com_email=email,
            com_content=content,
            com_approved=0,
            com_date=timezone.now(),
            com_ip=ip_address,
            com_agent=user_agent[:300],
        )

        url = reverse("article_detail", kwargs={"lg": lg, "slug": article_slug})
        return redirect(f"{url}?message=comment_added")
