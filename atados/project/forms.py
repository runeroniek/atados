# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from bootstrap_toolkit.widgets import BootstrapTextInput
from atados.project.models import (Project,
                                   ProjectDonation,
                                   ProjectWork,
                                   ProjectJob)


class ProjectCreateForm(forms.ModelForm):

    def __init__(self, nonprofit, user, *args, **kwargs):
        super(ProjectCreateForm, self).__init__(*args, **kwargs)

        self.nonprofit = nonprofit

        self.fields['email'].widget.attrs.update({
            'placeholder' : _('example@example.com')})

        self.fields['details'].widget.attrs.update({
            'placeholder' : _('Add more info about this project')})

        self.fields['causes'].empty_label = ""
        self.fields['causes'].label = _("Select one or more causes")
        self.fields['causes'].initial = set([cause.id for cause in nonprofit.causes.all()])

        self.fields['zipcode'].initial = nonprofit.zipcode
        self.fields['addressline'].initial = nonprofit.addressline
        self.fields['neighborhood'].initial = nonprofit.neighborhood
        self.fields['city'].initial = nonprofit.city

        self.fields['responsible'].initial = user.first_name
        self.fields['email'].initial = user.email
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        slug = slugify(name)
        if slug and self.instance.slug != slug and Project.objects.filter(
                slug=slug, nonprofit=self.nonprofit, deleted=False).count():
            raise forms.ValidationError(_('This name (or a very similar) is already is use.'))
        return name

class ProjectDonationCreateForm(ProjectCreateForm):

    class Meta:
        model = ProjectDonation
        exclude = ('nonprofit', 'slug', 'published', 'deleted', 'deleted_date')

class ProjectWorkCreateForm(ProjectCreateForm):

    def __init__(self, *args, **kwargs):
        super(ProjectWorkCreateForm, self).__init__(*args, **kwargs)
        self.fields['skills'].empty_label = ""
        self.fields['skills'].label = _("Select one or more skills")
        
    class Meta:
        model = ProjectWork
        exclude = ('nonprofit', 'slug', 'published', 'deleted', 'deleted_date')

class ProjectJobCreateForm(ProjectWorkCreateForm):

    class Meta:
        model = ProjectJob
        exclude = ('nonprofit', 'slug', 'published', 'deleted', 'deleted_date')

class ProjectPictureForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('image',)
