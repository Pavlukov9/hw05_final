from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from .utils import paginator


def index(request):
    posts = Post.objects.select_related('author', 'group')
    page_obj = paginator(request, posts)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator(request, posts)
    return render(request,
                  'posts/group_list.html',
                  {'group': group,
                   'page_obj': page_obj})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.all()
    page_obj = paginator(request, posts_list)
    following = False
    if request.user.is_authenticated:
        follow_list = Follow.objects.filter(user=request.user, author=author)
        following = follow_list.exists()
    return render(request,
                  'posts/profile.html',
                  {'page_obj': page_obj,
                   'author': author,
                   'following': following})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    return render(request,
                  'posts/post_detail.html',
                  {'post': post,
                   'requser': request.user,
                   'comments': comments,
                   'form': form})


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None,
                        files=request.FILES or None)
        if form.is_valid():
            create_post = form.save(commit=False)
            create_post.author_id = request.user.id
            create_post.save()
            return redirect('posts:profile', request.user)
        return render(request, 'posts/post_create.html', {'form': form})
    else:
        form = PostForm()
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.id != post.author_id:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/post_create.html', {'form': form,
                                                      'post': post,
                                                      'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, posts)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.id != author.id:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    else:
        return redirect('posts:profile', username)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user,
                          author=author).delete()
    return redirect('posts:follow_index')
