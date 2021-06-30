from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import View
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund
from .forms import CheckoutForm, CouponForm, RefundForm

import random
import string
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def item_list(request):
    context = {
        "items": Item.objects.all()
    }
    return render(request, "home.html", context)

def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
            break
    return valid
        

class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                "order": order,
                "couponform": CouponForm(),
                "DISPLAY_COUPON_FORM": True
            }
            shipping_address = Address.objects.filter(
                user=request.user,
                address_type="S",
                default=True
            )
            if shipping_address.exists():
                context.update({'default_shipping_address': shipping_address[0]})
                
            billing_address = Address.objects.filter(
                user=request.user,
                address_type="B",
                default=True
            )
            if billing_address.exists():
                context.update({'default_billing_address': billing_address[0]})

            return render(request, 'checkout-page.html', context)
        except ObjectDoesNotExist:
            messages.info(request, "You do not have an active order")
            return redirect("store:checkout")       
    
    def post(self, request, *args, **kwargs):
        form = CheckoutForm(request.POST or None)
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    print("Using the default shipping address")
                    address = Address.objects.filter(
                        user=request.user,
                        address_type="S",
                        default=True
                    )
                    if address.exists():
                        shipping_address = address[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(request, "No default shipping address available")
                        return redirect("store:checkout")
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    
                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                    
                        shipping_address = Address(
                            user = request.user,
                            street_address = shipping_address1,
                            apartment_address = shipping_address2,
                            country = shipping_country,
                            zip = shipping_zip,
                            address_type = "S"
                        )
                        shipping_address.save()
                        
                        order.shipping_address = shipping_address
                        order.save()
                        
                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(request, "Please fill in required shipping address fields")
                        return redirect("store:checkout")
                    
                use_default_billing = form.cleaned_data.get('use_default_billing')
                same_billing_address = form.cleaned_data.get("same_billing_address")
                
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = "B"
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                
                elif use_default_billing:
                    print("Using the default billing address")
                    address = Address.objects.filter(
                        user=request.user,
                        address_type="B",
                        default=True
                    )
                    if address.exists():
                        billing_address = address[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(request, "No default billing address available")
                        return redirect("store:checkout")
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')
                    
                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                    
                        billing_address = Address(
                            user = request.user,
                            street_address = billing_address1,
                            apartment_address = billing_address2,
                            country = billing_country,
                            zip = billing_zip,
                            address_type = "B"
                        )
                        billing_address.save()
                        
                        order.billing_address = billing_address
                        order.save()
                        
                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(request, "Please fill in required billing address fields")
                        return redirect("store:checkout")
                
                payment_option = form.cleaned_data.get('payment_option')
                
                if payment_option == "S":
                    return redirect("store:payment", payment_option="stripe")
                elif payment_option == "P":
                    return redirect("store:payment", payment_option="paypal")
                else:
                    messages.warning(request, "Invalid payment selected")
                    return redirect("store:checkout")
        except ObjectDoesNotExist:
            messages.warning(request, "You do not have an active order")
            return redirect("store:order-summary")


class PaymentView(LoginRequiredMixin, View):
    def get(self, request, *arg, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        if order.billing_address:
            context = {
                "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
                "order": order,
                "DISPLAY_COUPON_FORM": False
            }
            return render(request, 'payment.html', context)
        else:
            messages.warning(request, "You have not added a billing address")
            return redirect("store:checkout")
    def post(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        token = request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)
        print(amount)
        try:
            charge = stripe.Charge.create(
                amount=amount, # cents
                currency="usd",
                source=token
            )
            payment = Payment()
            payment.stripe_charge_id = charge["id"]
            payment.user = request.user
            payment.amount = order.get_total()
            payment.save()
            
            order_item = order.items.all()
            order_item.update(ordered=True)
            for item in order_item:
                item.save()
            
            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()
            
            messages.success(request, "Your order was successful")
            return redirect("/")
        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(request, f"{err.get('message')}")
            
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            print(e)
            messages.warning(self.request, "Invalid parameters")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network error")
            return redirect("/")

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.warning(
                self.request, "Something went wrong. You were not charged. Please try again.")
            return redirect("/")

        except Exception as e:
            # send an email to ourselves
            messages.warning(
                self.request, "A serious error occurred. We have been notifed.")
            return redirect("/")

        messages.warning(self.request, "Invalid data received")
        return redirect("/payment/stripe/")     


def product(request):
    context = {}
    return render(request, 'product.html', context)


class HomeView(ListView):
    model = Item
    template_name = "home.html"
    paginate_by = 10
    
    
class OrderSummary(LoginRequiredMixin, DetailView):
    def get(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            context = {
                'object': order
            }
            return render(request, "order_summary.html", context)
        except ObjectDoesNotExist:
            messages.warning(request, "You do not have an active order")
            return redirect("/")
        
    
    
class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"
    
@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, _ = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
        )
    order = Order.objects.filter(user=request.user, ordered=False)
    if order.exists():
        order = order[0]    
        
        # check if order item in order
        if order.items.filter(item__slug=slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("store:order-summary")
        else:
            messages.info(request, "This item was added to your cart.")
            order.items.add(order_item)
            return redirect("store:order-summary")
    else:
        order = Order.objects.create(user=request.user)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("store:order-summary")

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = Order.objects.filter(user=request.user, ordered=False)
    if order.exists():
        order = order[0]    
        
        # check if order item in order
        if order.items.filter(item__slug=slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user.id,
                ordered=False
                )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect("store:order-summary")
        else:
            # add a message saying the user doesnt have an order
            messages.info(request, "This item was not in your cart.")
            return redirect("store:product", slug=slug)            
    else:
        # add a message saying the user doesnt have an order
        messages.info(request, "You do not have an active order.")
        return redirect("store:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = Order.objects.filter(user=request.user, ordered=False)
    if order.exists():
        order = order[0]    
        
        # check if order item in order
        if order.items.filter(item__slug=slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user.id,
                ordered=False
                )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            
            messages.info(request, "This item quantity was updated.")
            return redirect("store:order-summary")
        else:
            # add a message saying the user doesnt have an order
            messages.info(request, "This item was not in your cart.")
            return redirect("store:product", slug=slug)            
    else:
        # add a message saying the user doesnt have an order
        messages.info(request, "You do not have an active order.")
        return redirect("store:product", slug=slug)
    
    
def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("store:checkout")
    
class AddCouponView(View):
    def post(self, request, *args, **kwargs):
        form = CouponForm(request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get("code")
                order = Order.objects.get(user=request.user, ordered=False)
                order.coupon = get_coupon(request, code)
                order.save()
                messages.success(request, "Successfully added coupon")
                return redirect("store:checkout")
            except ObjectDoesNotExist:
                messages.info(request, "You do not have an active order")
                return redirect("store:checkout")


class RequestRefundView(View):
    def get(self, request, *args, **kwargs):
        form = RefundForm()
        context = {
            "form": form
        }
        return render(request, "request_refund.html", context)
    
    def post(self, request, *args, **kwargs):
        form = RefundForm(request.POST or None)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')    
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                # edit the order
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()
                
                refund = Refund()
                refund.order = order
                refund.email = email
                refund.reason = message
                refund.save()
                
                messages.info(request, "Your request was received")
                return redirect("store:request-refund")
            except ObjectDoesNotExist:
                messages.info(request, "This order does not exist")
                return redirect("store:request-refund")