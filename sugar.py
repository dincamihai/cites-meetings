from functools import wraps
from flask import request, render_template

def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint \
                    .replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        decorated_function.original = f
        return decorated_function
    return decorator

from xhtml2pdf import pisa
from cStringIO import StringIO
def generate_pdf_from_html(html):
    result = StringIO()
    pdf = pisa.CreatePDF(html, result)
    assert pdf.err == 0, "Error generating pdf."
    return result.getvalue()
