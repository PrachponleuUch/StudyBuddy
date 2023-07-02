from django.shortcuts import render, redirect
from .forms import RoomForm, MyUserCreationForm, UserForm, SetPasswordForm, PasswordResetForm
from .models import User, Topic, Room, Message
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage

from .tokens import account_activation_token
from urllib.parse import quote
# Create your views here.

"""
Summary: handle functionalities for the home page that takes a HTTP request as its parameter
Use input from user to filter out rooms and rooms' messages being displayed
Get a count on the rooms after being filtered
Get all topics

Return:
Pass the above information in a form of a dictionary to base/home.html page
"""
def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(host__name__icontains=q) 
    )
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains = q))
    topics = Topic.objects.all()
    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)

"""
Summary: handle functionalities for the room page that takes a HTTP request and room primary key as its parameters
Get room object according to its id
Get all messages and participants in that room
If a message is post, create a new message obj, add the user as a participants of the room 
    redirect the user to the same room

Return:
Pass the above information in a form of a dictionary to base/room.html page
"""
def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'base/room.html', context)

"""
Summary: handle functionalities for the room form page that takes a HTTP request as its parameters
    and can only be access if the user is logged in
Get room's form from RoomForm class
Get all topics in Topic model
If user does a POST request, check if the topic already exists in the model else create a new one,
    create new room obj and redirect user to the home page

Return:
Pass the above information in a form of a dictionary to base/room_form.html page
"""
@login_required(login_url='login')
def createRoom (request):
    form = RoomForm()
    topics = Topic.objects.all()
    
    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name, encoded_name = quote(topic_name))
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),
            description = request.POST.get('description'),
            
        )
        return redirect('home')
    page = 'Create'
    context = {'form': form, 'topics': topics, 'page': page}
    return render(request, 'base/room_form.html', context)

"""
Summary: handle functionalities for the room form page that takes a HTTP request and room primary key 
    as its parameters and can only be access if the user is logged in and is the creator of the room

This function works the similarly to createRoom function with the difference being this function displays
    a prefill room's form using the instance of room id
"""
@login_required(login_url='login')
def updateRoom(request,pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user == room.host:
        if request.method == 'POST':
            topic_name = request.POST.get('topic')
            topic, created = Topic.objects.get_or_create(name=topic_name, encoded_name = quote(topic_name))
            room.name = request.POST.get('name')
            room.topic = topic
            room.description = request.POST.get('description')
            room.save()
            return redirect('home')
    else:
        messages.error(request, 'YOU ARE NOT ALLOWED')
    page = 'Update'
    context = {'form': form, 'topics': topics, 'room': room, 'page': page}
    return render(request, 'base/room_form.html', context)

"""
Summary: handle functionalities for the delete page that takes a HTTP request and room primary key 
    as its parameters and can only be access if the user is logged in 
Get room object according to its id
If user does a POST request and is the creator of the room, 
    delete the room and redirect user to the home page, else give an error message

Return:
Pass the above information in a form of a dictionary to base/delete.html page
"""
@login_required(login_url='login')
def deleteRoom(request,pk):
    room =Room.objects.get(id=pk)
    if request.user == room.host:
        if request.method == 'POST':
            room.delete()
            return redirect('home')
    else:
        messages.error(request, 'YOU ARE NOT ALLOWED')
    context = {'obj': room}
    return render(request, 'base/delete.html', context)

"""
Summary: handle functionalities for the login page that takes a HTTP request as its parameters
Get email and password from POST request
Try getting user obj according to the inputted email, else displays error message
Authenticate user according to the inputted email and password
If user exists, log the user in else displays error message

Return:
Pass the page variable in a form of a dictionary to base/login_register.html page
"""
def loginPage(request):
    page = 'login'
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        
        try: 
            user = User.objects.get(email=email)
        except:
            messages.error(request,'User does not exist')
            
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Email or Password is incorrect')
        
    context = {'page': page}
    return render(request, 'base/login_register.html', context)

"""
Summary: handle functionalities for the logout page that takes a HTTP request as its parameters

Return:
Redirect to home page
"""
def logoutPage(request):
    logout(request)
    return redirect('home')

"""
Summary: handle functionalities for the delete page that takes a HTTP request and message primary key 
    as its parameters and can only be access if the user is logged in 
Get message object according to its id
If user does a POST request and is the creator of the message, 
    delete the room and redirect user to the home page, else give an error message

Return:
Pass the above information in a form of a dictionary to base/delete.html page
"""
@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    if request.user == message.user:
        if request.method == 'POST':
            message.delete()
            return redirect('home')
    else:
        messages.error(request, 'YOU ARE NOT ALLOWED')
    context = {'obj': message}
    return render(request, 'base/delete.html', context)

"""
Summary: handle functionalities for the topic page that takes a HTTP request as its parameter
Use input from user to filter out topics being displayed

Return:
Pass the above information in a form of a dictionary to base/topics.html page
"""
def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(Q(name__icontains = q))
    context = {'topics': topics}
    return render(request, 'base/topics.html', context)

"""
Summary: handle functionalities for the activity page that takes a HTTP request as its parameter
Get all message objects from Message model

Return:
Pass the above information in a form of a dictionary to base/activity.html page
"""
def activityPage(request):
    room_messages = Message.objects.all()
    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)

"""
Summary: handle functionalities for the profile page that takes a HTTP request 
    and user primary key as its parameters 
    
Get user object using its primary key
Get all rooms that the user has participated in
Get all topics from its model
Get all messages that has been made by the user

Return:
Pass all above information in a form of a dictionary to base/profile.html page
"""
def profilePage(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    topics = Topic.objects.all()
    room_messages = user.message_set.all()
    context = {'user': user, 'rooms': rooms, 'topics': topics, 'room_messages': room_messages}
    return render(request, 'base/profile.html', context)

"""
Summary: handle functionalities for the edit user page that takes a HTTP request
    as its parameters and can only be access if the user is logged in 

Get the user object that did the HTTP request
Get an instance of a UserForm with prefilled information of the user
If user does a POST request, set form information to whatever is submitted by the user
Check if the form is valid, if so save and redirect to the user profile page

Return:
Pass the prefilled form in a form of a dictionary to base/edit-user.html
"""
@login_required(login_url='login')
def editProfile(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile', pk = user.id)
    context = {'form': form}
    return render(request, 'base/edit-user.html', context)

"""
Summary: handle functionalities for the register page that takes a HTTP request as its parameter
If user does a POST request, declare form variable to that instance of the form 
    else give the user an empty form
If form data is valid, create a user using the data without saving it to the database 
    and send an activation email using the inputted email to the user else give an error message
    
Return:
Pass the form in a form of a dictionary to base/login_register.html page
    Or redirect to home page
"""
def registerPage(request):
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST) 
        if form.is_valid():
            user = form.save(commit=False) # Wont be saved on db
            user.is_active = False # The user cant login without activated email acc
            user.username = user.username.lower()
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            
            return redirect('home')
        else:
            if form.errors.values() is None:
                messages.error(request, 'An error has occurred')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
    else:
        form = MyUserCreationForm()
    context = {'form': form}
    return render(request, 'base/login_register.html', context)

"""
Summary: function used to send user an activation email that takes a HTTP request, 
    a user obj and user's email as its parameter
Send activation request to user email using base/template_activate_account.html as the email's body
If the email is sent successfully notify the user with a success message else with an error message
"""
def activateEmail(request, user, to_email):
    mail_subject = "Activate your user account"
    message = render_to_string(
        "base/template_activate_account.html",
        {
        'user': user.username,
        'domain': get_current_site(request).domain, # Website domain
        'uid': urlsafe_base64_encode(force_bytes(user.pk)), # Encode user.pk to string
        'token': account_activation_token.make_token(user), # Make token for user
        'protocol': 'https' if request.is_secure() else 'http'
        }
    )
    email = EmailMessage(mail_subject, message, to={to_email})
    if email.send():
        messages.success(request, f"""Dear {user.username}, please go to your email {to_email} inbox and click on \
        received activation link to confirm and complete the registration. Note: Check your spam folder.""")    
    else:
        messages.error(request, f'Problem sending email to {to_email}, check if you typed it correctly.')

"""
Summary: function used to verify the account activation process that takes a HTTP request, 
    an encrypted uid and a token as its parameter
Try to decode the uid and use it to get user object from User model,
    if not possible, set user to None
If user exists and the token is valid, activate the account for the user and send a success message
    else send an error message

Return:
Redirect to login page if succeed else redirect to home page
"""
def activate(request, uidb64, token):
    try:
        # Decrypt uid to get user pk and check if user exist in our db
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        # Check if token has expired and activate user account
        user.is_active = True
        user.save()
        messages.success(request, "Thank you for your email confirmation. Now you can log into your account.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid")
    return redirect('home')

"""
Summary: handle functionalities for the password reset page that takes a HTTP request as its parameter
    and is required to be login

If user does a POST request, set the form to an instance of SetPasswordForm with the user inputted data
    else set it with current user data
If the form is valid, save the form information, prompt a success message 
    and redirect user to the login page else prompt an error message

Return:
Pass the prefilled form in a form of a dictionary to base/password_reset_confirm.html
"""
@login_required(login_url='login')
def password_change(request):
    user = request.user
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password has been changed successfully')
            return redirect('login')
        else: 
            for error in list(form.errors.values()):
                messages.error(request, error)
                
    form = SetPasswordForm(user)
    return render(request, 'base/password_reset_confirm.html', {'form': form})

"""
Summary: function used to send user an password reset confirmation email 
    that takes a HTTP request as its parameter
If user does a POST request, set the form to an instance of a PasswordResetForm with the user inputted data
    else form is set to an empty instance of a PasswordResetForm
If form is valid, check if the email is valid and get the user object using it
If user exists, send a password reset confirmation email to its email address
If the email is sent successfully, prompt a success message else an error message

Return:
Pass the form in a form of a dictionary to base/password_reset_confirm.html to render 
    If user doesn't do the POST request
"""
def password_reset_request(request):
    form = PasswordResetForm()
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            associated_user = User.objects.filter(Q(email=user_email)).first()
            if associated_user:
                subject = "Password Reset Request"
                message = render_to_string(
                    "base/template_reset_password.html",
                    {
                    'user': associated_user.username,
                    'domain': get_current_site(request).domain, # Website domain
                    'uid': urlsafe_base64_encode(force_bytes(associated_user.pk)), # Encode user.pk 
                    'token': account_activation_token.make_token(associated_user), # Make token for user
                    'protocol': 'https' if request.is_secure() else 'http'
                    }
                )
                email = EmailMessage(subject, message, to={associated_user.email})
                if email.send():
                    messages.success(
                        request,
                        """
                        Password reset sent
                        
                            We've emailed you instructions for setting your password, if an account exists with the email you entered. 
                            You should receive them shortly.If you don't receive an email, please make sure you've entered the email 
                            you registered with, and check your spam folder.
                        
                        """
                    )
                else:
                    messages.error(request,'Problem sending reset password email.')
            return redirect('home')
        
    return render(request,'base/password_reset_confirm.html',{'form':form})

"""
Summary: function used to verify the password reset process that takes a HTTP request, 
    an encrypted uid and a token as its parameter
This function follows the same logic as the activate function.
"""
def passwordResetConfirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user,request.POST)
            if form.is_valid():
                form.save()
        
                messages.success(
                    request,
                    """
                    Your password has been reset successfully.
                    """
                )
                return redirect('home')
                
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    
        form = SetPasswordForm(user)
        return render(request,'base/password_reset_confirm.html', {'form': form})
    
    else:
        messages.error(request,"Activation link is invalid")
    
    messages.error(request,'Something went wrong, redirecting to homepage')
    return redirect('home')


