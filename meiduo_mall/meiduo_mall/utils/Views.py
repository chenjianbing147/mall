from django.http import JsonResponse
from django.contrib.auth import authenticate


def my_decorate(fn):

    def inner(request, *args, **kwargs):
        if request.user.is_authenticated:
            return fn(request, *args, **kwargs)
        else:
            return JsonResponse({"code":400,
                                 "errmsg":"请登陆后重试"})

    return inner



class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls,*args, **kwargs):
        view = super().as_view()
        view = my_decorate(view)
        return view


