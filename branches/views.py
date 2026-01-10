from core import mixins
from .models import Branch
from . import tables

class BranchListView(mixins.HybridListView):
    model = Branch
    search_fields = ("name", "email")
    filterset_fields = ("name",)
    table_class = tables.BranchTable
    branch_filter = False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_branch"] = True
        return context
    


class BranchCreateView(mixins.HybridCreateView):
    model = Branch
    # template_name = "core/branch_form.html"


class BranchUpdateView(mixins.HybridUpdateView):
    model = Branch


class BranchDeleteView(mixins.HybridDeleteView):
    model = Branch
