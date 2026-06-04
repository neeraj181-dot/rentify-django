from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import Conversation, Message
from notifications.utils import create_notification


@login_required
def inbox_view(request):
    conversations = request.user.conversations.prefetch_related('participants', 'messages').order_by('-updated_at')
    # Annotate unread counts
    conv_data = []
    for conv in conversations:
        other = conv.get_other_participant(request.user)
        last_msg = conv.get_last_message()
        unread = conv.unread_count(request.user)
        conv_data.append({
            'conversation': conv,
            'other': other,
            'last_message': last_msg,
            'unread': unread,
        })
    total_unread = sum(c['unread'] for c in conv_data)
    return render(request, 'messaging/inbox.html', {
        'conv_data': conv_data,
        'total_unread': total_unread,
    })


@login_required
def conversation_view(request, conv_id):
    conversation = get_object_or_404(Conversation, pk=conv_id)
    if request.user not in conversation.participants.all():
        messages.error(request, "Access denied.")
        return redirect('inbox')

    # Mark messages as read
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.save()  # update updated_at
            other = conversation.get_other_participant(request.user)
            create_notification(
                recipient=other,
                sender=request.user,
                notification_type='new_message',
                message=f"New message from {request.user.username}",
                link=f'/messaging/{conversation.pk}/'
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': msg.id,
                    'content': msg.content,
                    'sender': msg.sender.username,
                    'time': msg.created_at.strftime('%H:%M'),
                    'is_mine': True,
                })
            return redirect('conversation', conv_id=conv_id)

    other = conversation.get_other_participant(request.user)
    msgs = conversation.messages.select_related('sender').all()

    # Build conv_data for sidebar
    all_convs = request.user.conversations.prefetch_related('participants', 'messages').order_by('-updated_at')
    conv_data = []
    for conv in all_convs:
        conv_data.append({
            'conversation': conv,
            'other': conv.get_other_participant(request.user),
            'last_message': conv.get_last_message(),
            'unread': conv.unread_count(request.user),
        })

    return render(request, 'messaging/conversation.html', {
        'conversation': conversation,
        'messages_list': msgs,
        'other': other,
        'conv_data': conv_data,
    })


@login_required
def start_conversation_view(request, username):
    other_user = get_object_or_404(User, username=username)
    if other_user == request.user:
        messages.error(request, "You can't message yourself.")
        return redirect('inbox')

    # Find existing or create new conversation
    existing = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=other_user)

    if existing.exists():
        conv = existing.first()
    else:
        conv = Conversation.objects.create()
        conv.participants.add(request.user, other_user)

    return redirect('conversation', conv_id=conv.pk)


@login_required
def get_new_messages(request, conv_id):
    """Polling endpoint to get new messages."""
    after_id = request.GET.get('after', 0)
    conversation = get_object_or_404(Conversation, pk=conv_id)
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'forbidden'}, status=403)

    new_msgs = conversation.messages.filter(id__gt=after_id).select_related('sender')
    new_msgs.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    data = [{
        'id': m.id,
        'content': m.content,
        'sender': m.sender.username,
        'time': m.created_at.strftime('%H:%M'),
        'is_mine': m.sender == request.user,
    } for m in new_msgs]
    return JsonResponse({'messages': data})
