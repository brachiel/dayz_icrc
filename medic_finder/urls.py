from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from medic_finder.models import Case
from django.contrib.auth.decorators import login_required, permission_required
    

urlpatterns = patterns('medic_finder.views',
    url(r'^(?:cases/new/?)?$', 'new_case_form'),
	url(r'^cases/list/?$', login_required(ListView.as_view(queryset=Case.objects.order_by('status'),
                                           context_object_name='all_cases',
                                           template_name='cases/list.html'))),
    url(r'^cases/show/(?P<slug>[0-9a-f]{40})/?$', DetailView.as_view(model=Case, slug_field='id_string', template_name='cases/detail.html')),
    url(r'^cases/show/(?P<pk>\d+)$', login_required(DetailView.as_view(model=Case, template_name='cases/detail.html'))),
	
	url(r'^logout/?$', 'logout'),
)
