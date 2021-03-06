from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404
from django.utils.decorators import classonlymethod
from atados.nonprofit.models import Nonprofit
from atados.nonprofit.forms import (NonprofitPictureForm,
                                    NonprofitFirstStepForm,
                                    NonprofitSecondStepForm,
                                    NonprofitThirdStepForm,
                                    NonprofitDetailsForm)


class NonprofitMixin(object):
    nonprofit = None
    only_owner = True

    def get_context_data(self, **kwargs):
        context = super(NonprofitMixin, self).get_context_data(**kwargs)
        context.update({'nonprofit': self.get_nonprofit()})
        return context

    def dispatch(self, request, *args, **kwargs):
        self.nonprofit = get_object_or_404(Nonprofit,
                                              slug=kwargs.get('nonprofit'))
        if self.only_owner and self.nonprofit.user != request.user:
            raise PermissionDenied
        return super(NonprofitMixin, self).dispatch(request,
                                                       *args, **kwargs)

    def get_nonprofit(self):
        return self.nonprofit

class NonprofitBaseView(NonprofitMixin, TemplateView):
    pass

class NonprofitHomeView(TemplateView):
    template_name = 'atados/nonprofit/home.html'

class NonprofitDetailsView(NonprofitBaseView):
    only_owner = False
    template_name = 'atados/nonprofit/details.html'

class NonprofitPictureUpdateView(NonprofitMixin, UpdateView):
    model = Nonprofit
    form_class=NonprofitPictureForm
    template_name='atados/nonprofit/picture.html'
    get_object = NonprofitMixin.get_nonprofit

class NonprofitDetailsUpdateView(NonprofitMixin, UpdateView):
    model = Nonprofit
    form_class=NonprofitDetailsForm
    template_name='atados/nonprofit/edit.html'
    get_object = NonprofitMixin.get_nonprofit

class NonprofitFirstStepView(NonprofitMixin, UpdateView):
    model = Nonprofit
    form_class=NonprofitFirstStepForm
    template_name='atados/nonprofit/first-step.html'
    get_object = NonprofitMixin.get_nonprofit
    
    def get_success_url(self):
        return reverse('nonprofit:second-step', args=(self.object.slug,))

class NonprofitSecondStepView(NonprofitMixin, UpdateView):
    model = Nonprofit
    form_class=NonprofitSecondStepForm
    template_name='atados/nonprofit/second-step.html'
    get_object = NonprofitMixin.get_nonprofit
    
    def get_success_url(self):
        return reverse('nonprofit:third-step', args=(self.object.slug,))
    
class NonprofitThirdStepView(NonprofitMixin, UpdateView):
    model = Nonprofit
    form_class=NonprofitThirdStepForm
    template_name='atados/nonprofit/third-step.html'
    get_object = NonprofitMixin.get_nonprofit

    def get_success_url(self):
        return reverse('atados:home',)
