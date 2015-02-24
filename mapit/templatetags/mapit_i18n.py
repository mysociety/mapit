"""An 'override' of the Django i18n templatetag file, with the blocktrans code
from Django 1.7 (with one import change for a function rename in 1.5, and with
a local trim_whitespace). This enables us to use "trimmed" in our templates on
older Django versions. BSD."""

from __future__ import unicode_literals
import re
import sys

from django.conf import settings
from django.template import Node, TemplateSyntaxError, Library
from django.template.base import TOKEN_TEXT, TOKEN_VAR
from django.template.defaulttags import token_kwargs
from django.utils import six
from django.utils import translation

from django.templatetags.i18n import *  # noqa
try:
    from django.template.base import render_value_in_context
except ImportError:
    # Renamed in Django 1.5
    from django.template.base import _render_value_in_context as render_value_in_context


trim_whitespace_re = re.compile('\s*\n\s*')


def trim_whitespace(s):
    return trim_whitespace_re.sub(' ', s.strip())


register = Library()
register.tag("get_available_languages", do_get_available_languages)
register.tag("get_language_info", do_get_language_info)
register.tag("get_language_info_list", do_get_language_info_list)
register.filter('language_name', language_name)
register.filter('language_name_local', language_name_local)
register.filter('language_bidi', language_bidi)
register.tag("get_current_language", do_get_current_language)
register.tag("get_current_language_bidi", do_get_current_language_bidi)
register.tag("trans", do_translate)
register.tag('language', language)


class BlockTranslateNode(Node):

    def __init__(
        self, extra_context, singular, plural=None, countervar=None,
            counter=None, message_context=None, trimmed=False):
        self.extra_context = extra_context
        self.singular = singular
        self.plural = plural
        self.countervar = countervar
        self.counter = counter
        self.message_context = message_context
        self.trimmed = trimmed

    def render_token_list(self, tokens):
        result = []
        vars = []
        for token in tokens:
            if token.token_type == TOKEN_TEXT:
                result.append(token.contents.replace('%', '%%'))
            elif token.token_type == TOKEN_VAR:
                result.append('%%(%s)s' % token.contents)
                vars.append(token.contents)
        msg = ''.join(result)
        if self.trimmed:
            msg = trim_whitespace(msg)
        return msg, vars

    def render(self, context, nested=False):
        if self.message_context:
            message_context = self.message_context.resolve(context)
        else:
            message_context = None
        tmp_context = {}
        for var, val in self.extra_context.items():
            tmp_context[var] = val.resolve(context)
        # Update() works like a push(), so corresponding context.pop() is at
        # the end of function
        context.update(tmp_context)
        singular, vars = self.render_token_list(self.singular)
        if self.plural and self.countervar and self.counter:
            count = self.counter.resolve(context)
            context[self.countervar] = count
            plural, plural_vars = self.render_token_list(self.plural)
            if message_context:
                result = translation.npgettext(message_context, singular,
                                               plural, count)
            else:
                result = translation.ungettext(singular, plural, count)
            vars.extend(plural_vars)
        else:
            if message_context:
                result = translation.pgettext(message_context, singular)
            else:
                result = translation.ugettext(singular)
        default_value = settings.TEMPLATE_STRING_IF_INVALID

        def render_value(key):
            if key in context:
                val = context[key]
            else:
                val = default_value % key if '%s' in default_value else default_value
            return render_value_in_context(val, context)

        data = dict((v, render_value(v)) for v in vars)
        context.pop()
        try:
            result = result % data
        except (KeyError, ValueError):
            if nested:
                # Either string is malformed, or it's a bug
                raise TemplateSyntaxError(
                    "'blocktrans' is unable to format "
                    "string returned by gettext: %r using %r" % (result, data))
            with translation.override(None):
                result = self.render(context, nested=True)
        return result


@register.tag("blocktrans")
def do_block_translate(parser, token):
    """
    This will translate a block of text with parameters.

    Usage::

        {% blocktrans with bar=foo|filter boo=baz|filter %}
        This is {{ bar }} and {{ boo }}.
        {% endblocktrans %}

    Additionally, this supports pluralization::

        {% blocktrans count count=var|length %}
        There is {{ count }} object.
        {% plural %}
        There are {{ count }} objects.
        {% endblocktrans %}

    This is much like ngettext, only in template syntax.

    The "var as value" legacy format is still supported::

        {% blocktrans with foo|filter as bar and baz|filter as boo %}
        {% blocktrans count var|length as count %}

    Contextual translations are supported::

        {% blocktrans with bar=foo|filter context "greeting" %}
            This is {{ bar }}.
        {% endblocktrans %}

    This is equivalent to calling pgettext/npgettext instead of
    (u)gettext/(u)ngettext.
    """
    bits = token.split_contents()

    options = {}
    remaining_bits = bits[1:]
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError('The %r option was specified more '
                                      'than once.' % option)
        if option == 'with':
            value = token_kwargs(remaining_bits, parser, support_legacy=True)
            if not value:
                raise TemplateSyntaxError('"with" in %r tag needs at least '
                                          'one keyword argument.' % bits[0])
        elif option == 'count':
            value = token_kwargs(remaining_bits, parser, support_legacy=True)
            if len(value) != 1:
                raise TemplateSyntaxError('"count" in %r tag expected exactly '
                                          'one keyword argument.' % bits[0])
        elif option == "context":
            try:
                value = remaining_bits.pop(0)
                value = parser.compile_filter(value)
            except Exception:
                msg = (
                    '"context" in %r tag expected '
                    'exactly one argument.') % bits[0]
                six.reraise(TemplateSyntaxError, TemplateSyntaxError(msg), sys.exc_info()[2])
        elif option == "trimmed":
            value = True
        else:
            raise TemplateSyntaxError('Unknown argument for %r tag: %r.' %
                                      (bits[0], option))
        options[option] = value

    if 'count' in options:
        countervar, counter = list(six.iteritems(options['count']))[0]
    else:
        countervar, counter = None, None
    if 'context' in options:
        message_context = options['context']
    else:
        message_context = None
    extra_context = options.get('with', {})

    trimmed = options.get("trimmed", False)

    singular = []
    plural = []
    while parser.tokens:
        token = parser.next_token()
        if token.token_type in (TOKEN_VAR, TOKEN_TEXT):
            singular.append(token)
        else:
            break
    if countervar and counter:
        if token.contents.strip() != 'plural':
            raise TemplateSyntaxError("'blocktrans' doesn't allow other block tags inside it")
        while parser.tokens:
            token = parser.next_token()
            if token.token_type in (TOKEN_VAR, TOKEN_TEXT):
                plural.append(token)
            else:
                break
    if token.contents.strip() != 'endblocktrans':
        raise TemplateSyntaxError("'blocktrans' doesn't allow other block tags (seen %r) inside it" % token.contents)

    return BlockTranslateNode(extra_context, singular, plural, countervar,
                              counter, message_context, trimmed=trimmed)
