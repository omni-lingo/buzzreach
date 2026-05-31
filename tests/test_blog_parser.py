"""Tests for the blog & forum comment parser (PARSE-003).

Uses saved HTML fixtures for WordPress, Disqus, Medium, and forum thread
layouts. Parser operates on raw HTML strings — no HTTP involved.
"""

from pathlib import Path

from contracts.extraction.extracted_content import ExtractedContent
from src.backend.services.blog_parser import (
    BlogComment,
    ForumReply,
    is_blog_url,
    parse_blog_post,
    parse_forum_thread,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures"
_WP_HTML = (_FIXTURE_DIR / "blog_wordpress.html").read_text(encoding="utf-8")
_DISQUS_HTML = (_FIXTURE_DIR / "blog_disqus.html").read_text(encoding="utf-8")
_MEDIUM_HTML = (_FIXTURE_DIR / "blog_medium.html").read_text(encoding="utf-8")
_FORUM_HTML = (_FIXTURE_DIR / "forum_thread.html").read_text(encoding="utf-8")

_WP_URL = "https://devblog.example.com/python-tips"
_DISQUS_URL = "https://techinsights.example.com/microservices"
_MEDIUM_URL = "https://medium.com/@nora-systems/rust-future"
_FORUM_URL = "https://devforums.example.com/thread/gcc-segfault"


class TestIsBlogUrl:
    """URL detection for blog platforms."""

    def test_medium_url(self) -> None:
        assert is_blog_url("https://medium.com/@user/post") is True

    def test_dev_to_url(self) -> None:
        assert is_blog_url("https://dev.to/user/post") is True

    def test_hashnode_url(self) -> None:
        assert is_blog_url("https://hashnode.dev/post") is True

    def test_substack_url(self) -> None:
        assert is_blog_url("https://newsletter.substack.com/p/post") is True

    def test_wordpress_com(self) -> None:
        assert is_blog_url("https://myblog.wordpress.com/post") is True

    def test_generic_url_not_detected(self) -> None:
        assert is_blog_url("https://example.com/page") is False

    def test_reddit_not_detected(self) -> None:
        assert is_blog_url("https://reddit.com/r/test") is False


class TestWordPressCommentParsing:
    """Parsing WordPress native comment system."""

    def test_extracts_title(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        assert result.title == "10 Python Tips Every Developer Should Know"

    def test_extracts_author(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        assert result.author == "Alice Martin"

    def test_extracts_publication_date(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        assert "2024-08-15" in result.pub_date

    def test_extracts_body_content(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        assert "Python" in result.body
        assert "List Comprehensions" in result.body

    def test_extracts_comment_count(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        assert result.comment_count == 5

    def test_extracts_comments(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        assert len(result.comments) >= 3

    def test_comment_has_author(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        authors = [c.author for c in result.comments]
        assert "Bob Developer" in authors

    def test_comment_has_text(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        bob = next(c for c in result.comments if c.author == "Bob Developer")
        assert "dataclasses" in bob.text

    def test_comment_has_date(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        bob = next(c for c in result.comments if c.author == "Bob Developer")
        assert bob.date != ""

    def test_comment_is_blog_comment_type(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        assert all(isinstance(c, BlogComment) for c in result.comments)

    def test_limits_comments_to_ten(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        assert len(result.comments) <= 10


class TestDisqusCommentParsing:
    """Parsing Disqus embedded comment system."""

    def test_extracts_title(self) -> None:
        result = parse_blog_post(_DISQUS_HTML, _DISQUS_URL)
        assert "Microservices" in result.title

    def test_extracts_author(self) -> None:
        result = parse_blog_post(_DISQUS_HTML, _DISQUS_URL)
        assert result.author == "Frank Architect"

    def test_extracts_comments(self) -> None:
        result = parse_blog_post(_DISQUS_HTML, _DISQUS_URL)
        assert len(result.comments) >= 2

    def test_disqus_comment_author(self) -> None:
        result = parse_blog_post(_DISQUS_HTML, _DISQUS_URL)
        authors = [c.author for c in result.comments]
        assert "Grace Ops" in authors

    def test_disqus_comment_text(self) -> None:
        result = parse_blog_post(_DISQUS_HTML, _DISQUS_URL)
        grace = next(c for c in result.comments if c.author == "Grace Ops")
        assert "monoliths" in grace.text

    def test_detects_disqus_system(self) -> None:
        result = parse_blog_post(_DISQUS_HTML, _DISQUS_URL)
        assert result.comment_count >= 3


class TestMediumParsing:
    """Parsing Medium-style article pages."""

    def test_extracts_title(self) -> None:
        result = parse_blog_post(_MEDIUM_HTML, _MEDIUM_URL)
        assert "Rust" in result.title

    def test_extracts_author(self) -> None:
        result = parse_blog_post(_MEDIUM_HTML, _MEDIUM_URL)
        assert result.author == "Nora Systems"

    def test_extracts_body(self) -> None:
        result = parse_blog_post(_MEDIUM_HTML, _MEDIUM_URL)
        assert "borrow checker" in result.body

    def test_extracts_responses(self) -> None:
        result = parse_blog_post(_MEDIUM_HTML, _MEDIUM_URL)
        assert len(result.comments) >= 2

    def test_response_author(self) -> None:
        result = parse_blog_post(_MEDIUM_HTML, _MEDIUM_URL)
        authors = [c.author for c in result.comments]
        assert "Oscar Perf" in authors


class TestForumThreadParsing:
    """Parsing forum thread layouts."""

    def test_extracts_title(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        assert "segfault" in result.title.lower()

    def test_extracts_author(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        assert result.author == "Jack Debug"

    def test_extracts_original_post(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        assert "GCC 13" in result.body

    def test_extracts_replies(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        assert len(result.replies) >= 3

    def test_reply_has_author(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        authors = [r.author for r in result.replies]
        assert "Kate Compiler" in authors

    def test_reply_has_text(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        kate = next(r for r in result.replies if r.author == "Kate Compiler")
        assert "GCC 13" in kate.text or "13.2" in kate.text

    def test_reply_has_date(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        kate = next(r for r in result.replies if r.author == "Kate Compiler")
        assert kate.date != ""

    def test_reply_is_forum_reply_type(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        assert all(isinstance(r, ForumReply) for r in result.replies)

    def test_limits_replies_to_ten(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        assert len(result.replies) <= 10


class TestBlogToExtractedContent:
    """BlogPost converts to ExtractedContent contract."""

    def test_converts_to_extracted_content(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        content = result.to_extracted_content()

        assert isinstance(content, ExtractedContent)
        assert content.url == _WP_URL
        assert "Python Tips" in content.title
        assert len(content.comments) >= 1

    def test_body_contains_article_text(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        content = result.to_extracted_content()
        assert "Python" in content.body

    def test_comments_include_author(self) -> None:
        result = parse_blog_post(_WP_HTML, _WP_URL)
        content = result.to_extracted_content()
        first_comment = content.comments[0]
        assert "Bob Developer" in first_comment


class TestForumToExtractedContent:
    """ForumThread converts to ExtractedContent contract."""

    def test_converts_to_extracted_content(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        content = result.to_extracted_content()

        assert isinstance(content, ExtractedContent)
        assert content.url == _FORUM_URL
        assert "segfault" in content.title.lower()
        assert len(content.comments) >= 1

    def test_body_contains_original_post(self) -> None:
        result = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        content = result.to_extracted_content()
        assert "GCC 13" in content.body


class TestFallbackBehavior:
    """Falls back gracefully on non-matching HTML."""

    def test_blog_fallback_on_plain_html(self) -> None:
        html = "<html><body><p>Just a normal page</p></body></html>"
        result = parse_blog_post(html, _WP_URL)
        assert result.title == ""
        assert result.comments == ()

    def test_blog_fallback_on_empty_html(self) -> None:
        result = parse_blog_post("", _WP_URL)
        assert result.title == ""
        assert result.comments == ()

    def test_forum_fallback_on_plain_html(self) -> None:
        html = "<html><body><p>Just a normal page</p></body></html>"
        result = parse_forum_thread(html, _FORUM_URL)
        assert result.title == ""
        assert result.replies == ()

    def test_forum_fallback_on_empty_html(self) -> None:
        result = parse_forum_thread("", _FORUM_URL)
        assert result.title == ""
        assert result.replies == ()


class TestCaching:
    """Same URL + HTML returns cached result."""

    def test_blog_same_input_returns_cached(self) -> None:
        result1 = parse_blog_post(_WP_HTML, _WP_URL)
        result2 = parse_blog_post(_WP_HTML, _WP_URL)
        assert result1 == result2

    def test_blog_different_input_returns_different(self) -> None:
        result1 = parse_blog_post(_WP_HTML, _WP_URL)
        result2 = parse_blog_post(_DISQUS_HTML, _DISQUS_URL)
        assert result1 != result2

    def test_forum_same_input_returns_cached(self) -> None:
        result1 = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        result2 = parse_forum_thread(_FORUM_HTML, _FORUM_URL)
        assert result1 == result2
