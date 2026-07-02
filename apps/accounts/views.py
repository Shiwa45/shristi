import random
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.urls import reverse
from .forms import UserProfileForm
from .models import User, OTPVerification

logger = logging.getLogger(__name__)


def _generate_otp():
    return str(random.randint(100000, 999999))


def _send_otp(phone, otp_code):
    logger.info(f"OTP for {phone}: {otp_code}")
    print(f"\n{'='*50}\nOTP for {phone}: {otp_code}\n{'='*50}\n")
    # TODO: Integrate SMS gateway (MSG91, Fast2SMS, Twilio) here


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next') or 'accounts:profile'
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form, 'next': request.GET.get('next', '')})


def register_view(request):
    if request.user.is_authenticated:
        next_url = request.GET.get('next', '')
        return redirect(next_url or 'accounts:profile')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        next_url = request.POST.get('next', request.GET.get('next', ''))

        errors = []
        if not all([first_name, email, phone, password]):
            errors.append('All required fields must be filled.')
        if password != password2:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists. Please login.')
        if not phone.isdigit() or len(phone) < 10:
            errors.append('Enter a valid 10-digit mobile number.')

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'accounts/register.html', {
                'form_data': request.POST,
                'next': next_url,
            })

        otp_code = _generate_otp()
        OTPVerification.objects.filter(phone=phone, is_used=False).delete()
        OTPVerification.objects.create(phone=phone, otp_code=otp_code)
        _send_otp(phone, otp_code)

        request.session['pending_registration'] = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'password': password,
        }
        request.session['otp_phone'] = phone

        messages.success(request, f'OTP sent to +91-{phone}. Please enter it below.')
        verify_url = reverse('accounts:verify_otp')
        if next_url:
            verify_url += f'?next={next_url}'
        return redirect(verify_url)

    return render(request, 'accounts/register.html', {
        'next': request.GET.get('next', ''),
    })


def verify_otp_view(request):
    phone = request.session.get('otp_phone')
    if not phone:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('accounts:register')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        next_url = request.POST.get('next', request.GET.get('next', ''))

        try:
            otp_obj = OTPVerification.objects.filter(
                phone=phone,
                otp_code=entered_otp,
                is_used=False
            ).latest('created_at')

            if otp_obj.is_expired():
                messages.error(request, 'OTP has expired. Please register again.')
                return redirect('accounts:register')

            reg_data = request.session.get('pending_registration', {})

            username = reg_data['email'].split('@')[0]
            base = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=reg_data['email'],
                password=reg_data['password'],
                first_name=reg_data.get('first_name', ''),
                last_name=reg_data.get('last_name', ''),
                phone=reg_data['phone'],
                is_verified=True,
            )

            otp_obj.is_used = True
            otp_obj.save()

            request.session.pop('pending_registration', None)
            request.session.pop('otp_phone', None)

            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account is verified.')

            if next_url:
                return redirect(next_url)
            return redirect('accounts:profile')

        except OTPVerification.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'accounts/verify_otp.html', {
        'phone': phone,
        'next': request.GET.get('next', ''),
    })


def resend_otp_view(request):
    phone = request.session.get('otp_phone')
    if not phone:
        return redirect('accounts:register')

    otp_code = _generate_otp()
    OTPVerification.objects.filter(phone=phone, is_used=False).delete()
    OTPVerification.objects.create(phone=phone, otp_code=otp_code)
    _send_otp(phone, otp_code)

    messages.success(request, f'New OTP sent to +91-{phone}.')
    next_url = request.GET.get('next', '')
    verify_url = reverse('accounts:verify_otp')
    if next_url:
        verify_url += f'?next={next_url}'
    return redirect(verify_url)


def ajax_register_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    phone = request.POST.get('phone', '').strip()
    password = request.POST.get('password', '')
    password2 = request.POST.get('password2', '')

    errors = []
    if not all([first_name, email, phone, password]):
        errors.append('All required fields must be filled.')
    if password != password2:
        errors.append('Passwords do not match.')
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long.')
    if User.objects.filter(email=email).exists():
        errors.append('An account with this email already exists. Please login.')
    if not phone.isdigit() or len(phone) < 10:
        errors.append('Enter a valid 10-digit mobile number.')

    if errors:
        return JsonResponse({'success': False, 'error': ' '.join(errors)})

    otp_code = _generate_otp()
    OTPVerification.objects.filter(phone=phone, is_used=False).delete()
    OTPVerification.objects.create(phone=phone, otp_code=otp_code)
    _send_otp(phone, otp_code)

    request.session['pending_registration'] = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'phone': phone,
        'password': password,
    }
    request.session['otp_phone'] = phone

    return JsonResponse({'success': True, 'require_otp': True, 'phone': phone})


def ajax_verify_otp_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    phone = request.session.get('otp_phone')
    if not phone:
        return JsonResponse({'success': False, 'error': 'Session expired. Please register again.'})

    entered_otp = request.POST.get('otp', '').strip()
    try:
        otp_obj = OTPVerification.objects.filter(
            phone=phone, otp_code=entered_otp, is_used=False
        ).latest('created_at')

        if otp_obj.is_expired():
            return JsonResponse({'success': False, 'error': 'OTP has expired. Please register again.'})

        reg_data = request.session.get('pending_registration', {})
        if not reg_data:
            return JsonResponse({'success': False, 'error': 'Session expired. Please register again.'})

        username = reg_data['email'].split('@')[0]
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=reg_data['email'],
            password=reg_data['password'],
            first_name=reg_data.get('first_name', ''),
            last_name=reg_data.get('last_name', ''),
            phone=reg_data['phone'],
            is_verified=True,
        )
        otp_obj.is_used = True
        otp_obj.save()

        request.session.pop('pending_registration', None)
        request.session.pop('otp_phone', None)

        login(request, user)
        return JsonResponse({'success': True, 'name': user.first_name})

    except OTPVerification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid OTP. Please try again.'})


def ajax_resend_otp_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    phone = request.session.get('otp_phone')
    if not phone:
        return JsonResponse({'success': False, 'error': 'Session expired.'})
    otp_code = _generate_otp()
    OTPVerification.objects.filter(phone=phone, is_used=False).delete()
    OTPVerification.objects.create(phone=phone, otp_code=otp_code)
    _send_otp(phone, otp_code)
    return JsonResponse({'success': True})


def ajax_login_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    user = authenticate(request, username=email, password=password)
    if user is None:
        # Try by email field since Django's default auth uses username
        try:
            u = User.objects.get(email=email)
            user = authenticate(request, username=u.username, password=password)
        except User.DoesNotExist:
            pass
    if user:
        login(request, user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid email or password.'})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    from apps.orders.models import QuoteRequest
    quotes = QuoteRequest.objects.filter(user=request.user).order_by('-created_at')[:10]

    return render(request, 'accounts/profile.html', {
        'form': form,
        'quotes': quotes,
    })
