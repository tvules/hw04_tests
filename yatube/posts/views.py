from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PostForm
from .models import Post, Group, User
from .utils import _get_page_obj
from yatube.settings import POSTS_PER_PAGE


def index(request):
    """Возвращает шаблон главной страницы."""
    posts = Post.objects.all()
    page_obj = _get_page_obj(request, posts, POSTS_PER_PAGE)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Возвращает шаблон странницы с постами определенной группы."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = _get_page_obj(request, posts, POSTS_PER_PAGE)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Возвращает шаблон страницы-профиля определенного пользователя."""
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = _get_page_obj(request, posts, POSTS_PER_PAGE)
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Возвращает шаблон страницы-обзор определенного поста."""
    post = get_object_or_404(Post, pk=post_id)
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Возвращает шаблон страницы с формой для создания нового поста."""
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    context = {
        'is_edit': False,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Возвращает шаблон страницы с формой для редактирования поста."""
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'is_edit': True,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)
