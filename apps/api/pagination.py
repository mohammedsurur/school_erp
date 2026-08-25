# apps/api/pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response   import Response


# ─────────────────────────────────────────────
#  Base mixin — adds meta envelope to response
# ─────────────────────────────────────────────

class EnvelopedPagination(PageNumberPagination):
    """
    Wraps paginated responses in a consistent envelope:

    {
        "meta": {
            "total":    <int>,
            "page":     <int>,
            "pages":    <int>,
            "per_page": <int>,
            "next":     <url|null>,
            "previous": <url|null>
        },
        "results": [ ... ]
    }
    """

    def get_paginated_response(self, data):
        return Response({
            'meta': {
                'total':    self.page.paginator.count,
                'page':     self.page.number,
                'pages':    self.page.paginator.num_pages,
                'per_page': self.get_page_size(self.request),
                'next':     self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'results': data,
        })

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'meta': {
                    'type': 'object',
                    'properties': {
                        'total':    {'type': 'integer'},
                        'page':     {'type': 'integer'},
                        'pages':    {'type': 'integer'},
                        'per_page': {'type': 'integer'},
                        'next':     {'type': 'string', 'nullable': True},
                        'previous': {'type': 'string', 'nullable': True},
                    }
                },
                'results': schema,
            }
        }


# ─────────────────────────────────────────────
#  Standard — 20 per page  (default)
# ─────────────────────────────────────────────

class StandardPagination(EnvelopedPagination):
    """
    Default for most endpoints.
    Client can override with ?page_size=N (max 100).
    """
    page_size              = 20
    page_size_query_param  = 'page_size'
    max_page_size          = 100
    page_query_param       = 'page'


# ─────────────────────────────────────────────
#  Large — 100 per page  (bulk / export endpoints)
# ─────────────────────────────────────────────

class LargePagination(EnvelopedPagination):
    """
    For endpoints that clients typically consume in bulk,
    e.g. student list, attendance records.
    Client can request up to 500 at once.
    """
    page_size              = 100
    page_size_query_param  = 'page_size'
    max_page_size          = 500
    page_query_param       = 'page'


# ─────────────────────────────────────────────
#  Small — 10 per page  (dashboard widgets)
# ─────────────────────────────────────────────

class SmallPagination(EnvelopedPagination):
    """
    For compact list widgets — notifications,
    recent activity feeds, etc.
    """
    page_size              = 10
    page_size_query_param  = 'page_size'
    max_page_size          = 50
    page_query_param       = 'page'