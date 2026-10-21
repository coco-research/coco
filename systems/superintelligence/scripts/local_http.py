"""Loopback-only HTTP opener, shared by meta_select.py and evals/skills/run.py. Stdlib only."""
import urllib.error
import urllib.request


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        err = urllib.error.HTTPError(req.full_url, code, msg, headers, fp)
        err.close()
        raise err


def local_opener():
    """Ignore proxy env vars and refuse redirects, so a request cannot leave the machine."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
