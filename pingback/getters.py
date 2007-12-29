import time
from datetime import time as t, date as d, datetime as dt

def post_get(year, month, day, slug, **kwargs):
    """ Returns Post object by date and slug.
    """
    from blog.models import Post
    date = d(*time.strptime(year + month + day, '%Y%m%d')[:3])
    post = Post.objects.filter(date__range=(dt.combine(date, t.min),
                                            dt.combine(date, t.max))
                               ).get(slug=slug)
    return post

