from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from flux.form import TicketForm, ReviewForm, FollowForm
from flux.models import Ticket, Review, UserFollows
from django.db.models import Q, Value, CharField
from django.contrib.auth.models import User
from itertools import chain


@login_required()
def flux(request):
    ticketes = Ticket.objects.all()
    reviewss = Review.objects.all()

    reviews = Review.objects.filter(Q(user__id__in=request.user.following.all().values_list('followed_user_id')) |
                                    Q(user_id=request.user.id))
    reviews = reviews.annotate(content_type=Value("REVIEW", CharField()))

    tickets = Ticket.objects.filter(Q(user__id__in=request.user.following.all().values_list('followed_user_id')) |
                                    Q(user_id=request.user.id))
    tickets = tickets.annotate(content_type=Value("TICKET", CharField()))

    posts = sorted(
        chain(reviews, tickets),
        key=lambda post: post.time_created,
        reverse=True
    )
    return render(request, 'flux/flux.html', context={'posts': posts, 'tickette' : ticketes, 'reviewss': reviewss})


@login_required()
def create_ticket(request):
    form = TicketForm()
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.user = request.user
            photo.save()
            form.save()
            return redirect('posts')
    return render(request, 'flux/create_ticket.html', context={'form': form})


@login_required()
def posts(request):

        posts = Ticket.objects.filter(user=request.user).order_by('-time_created')
        for row in Review.objects.all().reverse():
            if Review.objects.filter(ticket_id=row.ticket_id).count() > 1:
                row.delete()

        return render(request, 'flux/posts.html', {'posts': posts})


@login_required()
def update_review(request, p_id):
    ticket = Ticket.objects.get(id=p_id)
    review = Review.objects.get(ticket_id=p_id)
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES, instance=ticket)
        form_review = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid() and form_review.is_valid():
            photo = form.save(commit=False)
            photo.user = request.user
            photo.save()
            form.save()
            form_review.save()
            return redirect('posts')
    else:
        form = TicketForm(instance=ticket)
        form_review = ReviewForm(instance=review)
    return render(request, 'flux/ticket_update.html',
                  context={'form': form, 'form_review': form_review,
                           'review': review})


@login_required()
def ticket_only(request, p_id):
    tickets = Ticket.objects.get(id=p_id)
    if request.method == 'POST':
        forms = TicketForm(request.POST, request.FILES, instance=tickets)
        if forms.is_valid():
            photo = forms.save(commit=False)
            photo.uploader = request.user
            photo.save()
            forms.save()
            return redirect('posts')
    else:
        forms = TicketForm(instance=tickets)
    return render(request, 'flux/ticket_update.html', context={'form': forms, 'tickets': tickets})


@login_required()
def create_critic_no_answer(request):
    form = TicketForm()
    form_rating = ReviewForm()
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        form_rating = ReviewForm(request.POST)

        if form.is_valid() and form_rating.is_valid():
            form_critique = form.save(commit=False)
            form_critique.user = request.user
            form_critique.save()
            form_critique_rating = form_rating.save(commit=False)
            form_critique_rating.user = request.user
            form_critique_rating.ticket = form_critique
            form_critique_rating.save()
            return redirect('posts')
    return render(request, 'flux/create_critique.html',
                  context={'form': form, 'form_rating': form_rating})


@login_required()
def delete_posts(request, p_id):
    ticket = Ticket.objects.get(id=p_id)
    if request.method == 'POST':
        ticket.delete()
        return redirect('posts')
    return render(request, 'flux/posts_delete.html', context={'ticket': ticket})


def create_review_for_post(request, p_id):
    ticket = Ticket.objects.get(id=p_id)
    review = ReviewForm()
    if request.method == 'POST':
        review = ReviewForm(request.POST)
        if review.is_valid():
            form_critique = review.save(commit=False)
            form_critique.user = request.user
            form_critique.ticket = ticket
            form_critique.save()
            return redirect('posts')
    else:
        review = ReviewForm()
    return render(request, 'flux/create_critique_for_post.html',
                  context={'ticket': ticket,
                           'review': review})


@login_required()
def follow_user(request):
    form = FollowForm(instance=request.user)
    if request.method == 'POST':
        if request.POST.get('search'):
            search = request.POST['search']
            follower = User.objects.get(Q(username__contains=search) & ~Q(username=request.user))
            follow = UserFollows(followed_user_id=follower.id, user_id=request.user.id)
            follow.save()
            return redirect('search')
    else:
        following = UserFollows.objects.filter(user=request.user)
        followers = UserFollows.objects.filter(followed_user=request.user)

        return render(request, 'flux/followers_search.html', {'following': following, 'followers': followers})


@login_required
def delete_user_follow(request, follow_id):
    user_follows = get_object_or_404(UserFollows, pk=follow_id)
    user_follows.delete()
    return redirect('search')
