from django.contrib import admin
from .models import Service, Worker, Hire, Review, ContractorProfile, BulkRequest, BulkReview

class WorkerAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'rating', 'jobs_completed', 'success_rate')
    search_fields = ('user__username', 'service__name')

class ContractorProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'rating', 'projects_completed', 'success_rate')
    search_fields = ('company_name',)

admin.site.register(Service)
admin.site.register(Worker, WorkerAdmin)
admin.site.register(Hire)
admin.site.register(Review)
admin.site.register(ContractorProfile, ContractorProfileAdmin)
admin.site.register(BulkRequest)
admin.site.register(BulkReview)
