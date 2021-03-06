from django.http import Http404
from django.views.generic import TemplateView, View
from django.views.generic.edit import (CreateView, ModelFormMixin, UpdateView,
                                       DeleteView)
from django.views.generic.detail import DetailView
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _, ugettext as __
from atados.core.views import JSONResponseMixin
from atados.volunteer.models import Volunteer
from atados.project.models import (Project, ProjectDonation, ProjectWork,
                                   ProjectJob, Apply, Availability)
from atados.nonprofit.models import Nonprofit
from atados.nonprofit.views import NonprofitMixin
from atados.project.forms import (ProjectDonationCreateForm,
                                  ProjectWorkCreateForm,
                                  ProjectJobCreateForm,
                                  ProjectPictureForm)


class AvailabilityMixin(object):
    availability_list = None

    def __init__(self, *args, **kwargs):
        super(AvailabilityMixin, self).__init__(*args, **kwargs)
        self.availability_list = Availability.objects.all()


    def get_context_data(self, **kwargs):
        context = super(AvailabilityMixin, self).get_context_data(**kwargs)
        context.update({'availability_list': self.availability_list})
        return context

class ProjectMixin(NonprofitMixin):
    project = None

    def get_context_data(self, **kwargs):
        context = super(ProjectMixin, self).get_context_data(**kwargs)
        context.update({'project': self.get_project()})
        return context

    def get_project(self):
        if self.project is None:
            try:
                self.project = ProjectWork.objects.get(
                    nonprofit=self.get_nonprofit(),
                    slug=self.kwargs.get('project'),
                    deleted=False)
            except ProjectWork.DoesNotExist:
                try:
                    self.project = ProjectDonation.objects.get(
                        nonprofit=self.get_nonprofit(),
                        slug=self.kwargs.get('project'))
                except ProjectDonation.DoesNotExist:
                    raise Http404

        return self.project

class ProjectModelMixin(NonprofitMixin, AvailabilityMixin):
    model=Project

    def get_form_kwargs(self):
        kwargs = super(ProjectModelMixin, self).get_form_kwargs()
        kwargs.update({
            'nonprofit': self.get_nonprofit(),
            'user': self.request.user,
        })
        return kwargs

    def form_valid(self, form):
        model = form.save(commit=False)
        if self.request.user.is_authenticated():
            model.nonprofit = Nonprofit.objects.get(user=self.request.user)
            model.slug = slugify(model.name)
        else:
            forms.ValidationError("Authentication required")
        return super(ProjectModelMixin, self).form_valid(form)

class ProjectUpdateView(ProjectModelMixin, ProjectMixin, UpdateView):
    template_name = 'atados/project/edit.html'

    def get_form_class(self):
        if isinstance(self.object, ProjectWork):
            return ProjectWorkCreateForm
        elif isinstance(self.object, ProjectJob):
            return ProjectJobCreateForm
        elif isinstance(self.object, ProjectDonation):
            return ProjectDonationCreateForm
        else:
            raise Http404
    
    def get_context_data(self, **kwargs):
        context = super(ProjectUpdateView, self).get_context_data(**kwargs)
        context.update({'form_template': ('atados/project/form-%s.html' % self.get_project().get_project_type())})
        return context
        
    def get_success_url(self):
        return reverse('project:edit',
                       args=[self.object.nonprofit.slug, self.object.slug])

    get_object = ProjectMixin.get_project

class ProjectCreateView(ProjectModelMixin, CreateView):
    pass

class ProjectDonationCreateView(ProjectCreateView):
    form_class=ProjectDonationCreateForm
    template_name='atados/project/new-donation.html'

class ProjectWorkCreateView(ProjectCreateView):
    form_class=ProjectWorkCreateForm
    template_name='atados/project/new-work.html'

class ProjectJobCreateView(ProjectWorkCreateView):
    form_class=ProjectJobCreateForm
    template_name='atados/project/new-job.html'

class ProjectDetailsView(ProjectMixin, DetailView):
    only_owner=False

    def get_volunteer(self):
        if self.request.user.is_authenticated():
            try:
                return Volunteer.objects.get(user=self.request.user)
            except Volunteer.DoesNotExist:
                pass
        return None

    def get_context_data(self, **kwargs):
        context = super(ProjectDetailsView, self).get_context_data(**kwargs)
        
        volunteer = self.get_volunteer()

        if volunteer is not None:
            try:
                context.update({'apply': Apply.objects.get(
                    project=self.get_project(),
                    volunteer=volunteer)})
            except Apply.DoesNotExist:
                pass

        return context

    def get_template_names(self):
        if isinstance(self.object, ProjectDonation):
            return 'atados/project/details-donation.html'
        if isinstance(self.object, ProjectWork):
            if self.object.weekly_hours > 0:
                return 'atados/project/details-job.html'
            else:
                return 'atados/project/details-work.html'
        raise Http404

    get_object = ProjectMixin.get_project

class ProjectCollaboratorsView(ProjectMixin, TemplateView):
    template_name = 'atados/project/collaborators.html'

class ProjectDeleteView(ProjectMixin, TemplateView):
    template_name = 'atados/project/delete.html'

class ProjectApplyView(ProjectMixin, JSONResponseMixin, View):
    only_owner = False

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            context = {'success': False,
                       'errors': __('Login required')}
            return self.render_to_response(context)

        Apply(project=self.get_project(), volunteer=Volunteer.objects.get(user=request.user)).save()

        context = {'success': True,
                   'msg': ''}
        return self.render_to_response(context)

    get = post

class ProjectPictureUpdateView(ProjectMixin, UpdateView):
    model = Project
    form_class=ProjectPictureForm
    template_name='atados/project/picture.html'
    get_object = ProjectMixin.get_project

class ProjectDeleteView(ProjectMixin, DeleteView):
    get_object = ProjectMixin.get_project
    template_name='atados/project/delete.html'

    def get_success_url(self):
        messages.info(self.request, _('Project was successfully deleted.'))
        return reverse('atados:home')
