# Just example
ENABLE_PINGBACK = True

PINGBACK_SERVER = {
    'post_detail': 'pingback.getters.post_get',
    }
PINGBACK_RESPONSE_LENGTH = 200

PINGBACK_CLIENT = {
    'blog.post': {'content': 'html', 'url': 'get_absolute_url'},
    }
