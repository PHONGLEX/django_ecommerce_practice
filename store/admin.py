from django.contrib import admin

from .models import Item, OrderItem, Order, Payment, Coupon, Refund, Address


def make_refund_accepted(modeladmin, request, queryset):
    """[summary]

    Args:
        modeladmin ([type]): [description]
        request ([type]): [description]
        queryset ([type]): [description]
    """
    queryset.update(refund_requested=False, refund_granted=True)
make_refund_accepted.short_description = "Update order to refund granted"


class OrderAdmin(admin.ModelAdmin):
    list_display = ["user", "ordered", "being_delivered",
                "received",
                "refund_requested",
                "refund_granted",
                "billing_address", 
                "shipping_address",
                "payment", 
                "coupon"]
    list_display_links = ['user', "billing_address"
                          , "shipping_address"
                          , "payment", "coupon"]
    list_filter = ["ordered", "being_delivered",
                "received",
                "refund_requested",
                "refund_granted"]
    search_fields = ['user__username', "ref_code"]
    actions = [make_refund_accepted]
    
    
class AddressAdmin(admin.ModelAdmin):
    list_display = [ "user", "street_address", "apartment_address"
                    , "country", "zip", "address_type", "default" ]
    list_filter = ["country", "default", "address_type"]
    search_fields = ["user__username", "street_address"
                     , "apartment_address", "zip"]
    

admin.site.register((Item, OrderItem, Payment, Coupon, Refund, ))
admin.site.register(Address, AddressAdmin)
admin.site.register(Order, OrderAdmin)
