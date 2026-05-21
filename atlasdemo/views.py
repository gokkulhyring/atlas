from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CompareUploadForm, SignupForm
from .models import ComparisonJob
from .tasks import run_comparison


def index(request):
    """Root URL: send authenticated users to /compare/, others to /login/."""
    if request.user.is_authenticated:
        return redirect('compare')
    return redirect('login')


def signup(request):
    """Create a new user and log them in immediately on success."""
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('compare')
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def compare(request):
    """Show the upload form; on POST, persist files to the DB and enqueue a task."""
    if request.method == 'POST':
        form = CompareUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_a = form.cleaned_data['file_a']
            file_b = form.cleaned_data['file_b']
            job = ComparisonJob.objects.create(
                user=request.user,
                file_a_name=file_a.name,
                file_a_data=file_a.read(),
                file_b_name=file_b.name,
                file_b_data=file_b.read(),
            )
            run_comparison.delay(str(job.id))
            return redirect('comparison_status', job_id=job.id)
    else:
        form = CompareUploadForm()
    return render(request, 'atlasdemo/compare.html', {'form': form})


@login_required
def comparison_status(request, job_id):
    """Poll endpoint: re-renders every 2s until status is `done` or `failed`."""
    job = get_object_or_404(ComparisonJob, pk=job_id, user=request.user)

    if job.status == ComparisonJob.STATUS_FAILED:
        return render(
            request,
            'atlasdemo/compare.html',
            {'form': CompareUploadForm(), 'error': job.error or 'Comparison failed.'},
        )

    if job.status == ComparisonJob.STATUS_DONE:
        return render(
            request,
            'atlasdemo/results.html',
            {
                'result': job.result_json,
                'file_a_name': job.file_a_name,
                'file_b_name': job.file_b_name,
            },
        )

    return render(request, 'atlasdemo/processing.html', {'job': job})
