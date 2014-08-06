from __future__ import unicode_literals

import re
try:
    from html import escape
except ImportError:
    def escape(s, quote=True):
        s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>','&gt;')
        if quote:
            s = s.replace('"', '&quot;').replace("'", '&#x27;')
        return s

# Using StringIO makes the source uglier, but also faster.
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

__all__ = ['markdown']

def markdown(text):
    if not text.lstrip('\n'): return ''
    return Markdown(text).html().getvalue()


LIST_SPECIFIERS = ('*', '+', '-')
ORDERED_LIST = 1
UNORDERED_LIST = 2

# regexs
# FIXME I hate using all these negative lookbehinds!
# Actually, I don't like using re at all... but it's comparatively faster.

LIST_1 = re.compile('{0}{0}(.+?{0}?){0}{0}'.format('(?<!\\\)\*'))
LIST_2 = re.compile('{0}(.+?){0}'.format('(?<!\\\)\*'))
LIST_3 = re.compile('{0}{0}(.+?{0}?){0}{0}'.format('(?<!\\\)\_'))
LIST_4 = re.compile('{0}(.+?){0}'.format('(?<!\\\)\_'))
# using lambdas here is faster than r'<em>\1<em>' oddly enough
LIST_s = lambda m:'<strong>{0}</strong>'.format(m.group(1))
LIST_em = lambda m:'<em>{0}</em>'.format(m.group(1))
CODE_SPAN = re.compile('(?:`(`.+?`)`)|(`.*?`)')
INLINE_HTML = re.compile('(<\S[^<]*?>)')
AMP = re.compile('&(?!\w+;)')
HR = re.compile('^([- ]{3,}|[* ]{3,}|[_ ]{3,})$')
HREF = re.compile('<(http\S+)>')
HREF_inline = lambda m:'<a href="{0}">{0}</a>'.format(m.group(1))

# [text](/url/ "title")
URL = re.compile('((?<!\\\)\!)?\[(.+?)\]\((.*?)(?:\s+\"(.*?)\")?\s*\)',
        re.DOTALL)
def URL_a (m):
    if m.group(1): return IMG_img(m)
    return '<a href="{1}"{2}>{0}</a>'.format(m.group(2), m.group(3),
            ' title="{0}"'.format(escape(m.group(4))) if m.group(4) else '')

# [id][ID]
URL_REF = re.compile('((?<!\\\)\!)?(?<!\\\)\[([^\[\]\\\]+?|(?:.*?\[.*?\].*?)+)\](?:\s*\[([^\[\]\\\]*?)\])?', re.DOTALL)

# [id]: /url/ "title"
URL_DEF = re.compile('\s{0,3}\[([^\[\]\\\]+?)\]:\s*([^ \"\\\]+)\s*(?:\"([^\[\]\\\]+)\")?')

# ![alt](/url/ "title")
IMG = re.compile('((?<!\\\)\!)\[(.+?)\]\((.*?)(?:\s+\"(.*?)\")?\s*\)', re.DOTALL)
IMG_img = lambda m:'<img src="{1}"{2} alt="{0}" />'.format(m.group(2),
        m.group(3),
        ' title="{0}"'.format(escape(m.group(4))) if m.group(4) else '')

# [id]: /url/to/image/ "title"
IMG_REF = re.compile('((?<!\\\)\!)(?<!\\\)\[([^\[\]\\\]+?)\](?:\s*\[([^\[\]\\\]*?)\])?')

FIND_CODE_SPAN = re.compile(r'(?<!\\)`')
FIND_INLINE_HTML = re.compile(r'(?<!\\)<')
FIND_GT = re.compile(r'(?<!\\)>')
FIND_LT = re.compile(r'(?<!\\)<')
FIND_BS = re.compile(r'(?<!\\)\\')

class Markdown:
    def __init__(self, text, parent_markdown=None, in_li=False):
        if isinstance(text, str):
            self.lines = text.expandtabs(4).split('\n')
        else:
            self.lines = text
        self.num_empty_lines = 0
        self.in_li = in_li
        if parent_markdown:
            self.urls = parent_markdown.urls
        else:
            self.urls = {}

    def html(self, r=None):
        r = r or StringIO()
        for b in self.blocks:
            b.html(r)
        return r

    @property
    def blocks(self):
        """
        self.lines parsed into Nodes (blocks of related lines).
        """
        # Gather url defs
        for i,l in enumerate(self.lines):
            if '[' in l and ':' in l:
                m = URL_DEF.match(l)
                if m:
                    k, url, title = m.groups()
                    self.urls[k] = (url, escape(title) if title else '')
                    self.lines[i] = None

        # TODO this could be prettier
        b = []
        block_indent = None
        last_is_block = False
        last_was_blank = True
        i = 0
        block_type = None
        BLOCKQUOTE = 1
        LIST = 2
        for l in self.lines:
            if l is None: continue
            starts_with_block_def = False
            stripped = l.lstrip()
            if not stripped:
                last_was_blank = True
                self.num_empty_lines += 1
            else:
                i = len(l) - len(stripped)
                if b and last_was_blank and (i < block_indent or (
                            block_indent < 4 and not last_is_block)):
                    # Block was eneded with a blank line or dedent.
                    yield Node(b, self, block_indent)
                    b = []
                    block_indent = None
                    last_is_block = False

                # The rest of this only needs to be done if it's not in a code
                # block. (indention level less than 4)
                if i < 4:
                    # atx-style header
                    if b and not last_is_block and (not stripped.strip('-') or\
                              not stripped.strip('=')):
                        ht = b.pop()
                        if '\n' in ht:
                            f,ht = ht.rsplit('\n', 1)
                            b.append(f)
                        if b:
                            yield Node(b, self, block_indent)
                        yield HNode(ht, 1 if stripped[0] == '=' else 2)
                        b = []
                        continue

                    # setext-style header
                    if not last_is_block and l[0] == '#':
                        if b:
                            yield Node(b, self, block_indent)
                            b = []
                        yield HNode(l)
                        continue

                    # hr
                    if HR.match(stripped):
                        if b:
                            yield Node(b, self, block_indent)
                            b = []
                        yield HRNode()

                        last_is_block = False
                        last_was_blank = True
                        continue

                    # Check to see if this line specifies a block (list etc)
                    try:
                        first_part, txt = stripped.split(' ', 1)
                    except ValueError:
                        first_part = None

                    if first_part and (last_is_block or last_was_blank or\
                            self.in_li) and (
                            (first_part in LIST_SPECIFIERS or \
                            first_part[:-1].isdigit())):
                        starts_with_block_def = True
                        if not last_was_blank and self.in_li and b and not\
                                last_is_block:
                            yield Node(b, self, block_indent)
                            b = []
                        last_is_block = True
                        listtype = ORDERED_LIST if\
                            first_part[-1] == '.' else UNORDERED_LIST
                        l = [listtype, txt]
                        block_type = LIST

                    elif stripped[0] == '>':
                        starts_with_block_def = True
                        if last_is_block and block_type != BLOCKQUOTE:
                            last_is_block = False
                            if b:
                                yield Node(b, self, block_indent)
                                b = []

                        if not last_is_block:
                            if b:
                                yield Node(b, self, block_indent)
                                b = []
                            last_is_block = True
                            block_type = BLOCKQUOTE

                    elif last_was_blank and not (last_is_block and i > 1):
                        # No block defs were made and the last line was blank.
                        # That means this line starts a new paragraph.
                        # UNLESS it's part of a list item.
                        if b:
                            yield Node(b, self, block_indent)
                            b = []
                        last_is_block = False

                if block_indent is None:
                    block_indent = i
                last_was_blank = False
            if i >= 4 or stripped or last_is_block:
                # We wan't to ignore empty lines unless they are in a block.
                if not last_is_block and not starts_with_block_def and i < 4 and b:
                    if isinstance(b[-1], list):
                        b[-1][-1] += '\n'+l.lstrip()
                    else:
                        b[-1] += '\n'+l.lstrip()
                else:
                    b.append(l)
        if b:
            yield Node(b, self, block_indent)


class HRNode:
    def html(self, strio):
        strio.write('<hr />\n')

class HNode:
    def __init__(self, line, level=None):
        self.line = line.lstrip('#')
        self.level = level or len(line) - len(self.line)
        self.line = self.line.strip(' #')

    def html(self, strio):
        strio.write('<h{0}>{1}</h{0}>\n'.format(self.level, self.line))

class Node:
    """
    A Node is a grouping of related lines; such as a list, codeblock,
    paragraph etc.
    """
    def __init__(self, lines, markdown, indent):
        self.lines = lines
        self.markdown = markdown
        self.is_blockquote = False
        self.indent = indent
        if type(lines[0][0]) is int:
            # This Node is a list.
            self.list_type = lines[0][0]
            self.is_list = True
        else:
            # It's not a list, check indention level.
            self.is_list = False

            if self.indent:
                # Dedent all lines up to 4 spaces.
                i = min(4, self.indent)
                self.lines = [l[i:] for l in self.lines]

        # If we're a code block don't process further.
        if self.indent < 4:
            if not self.is_list and self.lines[0][0] == '>':
                self.is_blockquote = True
                # TODO put this in a map function?
                nl = []
                for l in self.lines:
                    s = l.lstrip()
                    if s and s.startswith('> '):
                        nl.append(s[2:])
                    elif s and s[0] == '>':
                        nl.append(s[1:])
                    else:
                        nl.append(l)
                self.lines = nl

            elif self.is_list:
                # reduce mutli line block elements into single lines.
                # (support for block-level wrapping)
                nl = []
                for l in self.lines:
                    if not l:
                        nl[-1] += '\n'
                    elif type(l[0]) is int:
                        nl.append(l[1])
                    else:
                        nl[-1] += '\n'+l[min(4, len(l)-len(l.lstrip())):]
                self.lines = nl

            else:
                # HACK to put html comments on a single "line" so it can be
                # parsed as inline html.
                nl = []
                comment_started = False
                for l in self.lines:
                    if comment_started:
                        nl[-1] += '\n'+l
                        if '-->' in l:
                            comment_started = False
                    else:
                        if '<!--' in self.lines:
                            comment_started = True
                        nl.append(l)
                self.lines = nl


    def html(self, strio):
        if self.indent >= 4:
            strio.write('<pre><code>')
            strio.write(escape('\n'.join(self.lines), quote=False).rstrip('\n'))
            strio.write('</code></pre>\n')

        elif self.is_blockquote:
            strio.write('<blockquote>\n')
            Markdown(self.lines, self.markdown).html(strio)
            strio.write('\n</blockquote>\n')

        elif self.is_list:
            # This feels silly
            if self.list_type == UNORDERED_LIST:
                self.markdown_lines(strio, wrap='ul')
            else:
                self.markdown_lines(strio, wrap='ol')

        elif not self.markdown.in_li or self.markdown.num_empty_lines:
            self.markdown_lines(strio, wrap='p')
        else:
            self.markdown_lines(strio)


    def _groupby(self, strio, f, s, l, regex, on_exact_match=None):
        if s not in l: return False
        groups = tuple(i for i in regex.split(l) if i)
        #if len(groups) == 1: return False
        for i in groups:
            if i[0] == f and i[-1] == s:
                if on_exact_match:
                    strio.write(on_exact_match(i))
                else:
                    strio.write(i)
            else:
                self.markdown_lines(strio, [i])
        return True


    def markdown_lines(self, strio, lines=None, wrap=None):
        if not lines: lines = self.lines
        first = True
        if wrap and lines[0][0] == '<' and INLINE_HTML.match(lines[0]) and\
                lines[-1].rstrip()[-1] == '>':
            wrap = None

        if wrap:
            strio.write('<'+wrap+'>')

        for l in lines:
            if first:
                first = False
            else:
                strio.write('\n')
            if self.is_list:
                strio.write('<li>')
                Markdown(l.strip().split('\n'), self.markdown, in_li=True).html(strio)
                strio.write('</li>')
                continue

            has_bs = '\\' in l

            if has_bs:
                if '`' in l:
                    i1 = FIND_CODE_SPAN.search(l)
                    i1 = i1.start() if i1 else -1
                else: i1 = -1

                if '<' in l and '>' in l:
                    i2 = FIND_INLINE_HTML.search(l)
                    i2 = i2.start() if i2 else -1
                else: i2 = -1
            else:
                i1 = l.index('`') if '`' in l else -1 
                i2 = l.index('<') if '<' in l else -1

            
            if i1 == -1 and i2 == -1:
                # nither code span nor inlined html
                if has_bs:
                    if '&' in l:
                        l = AMP.sub('&amp;', l)
                    if '>' in l:
                        l = FIND_GT.sub('&gt;', l)
                    if '<' in l:
                        l = FIND_LT.sub('&lt;', l)
                else:
                    l = AMP.sub('&amp;', l.replace('>', '&gt;'))

                # Check for strong and em
                if '*' in l:
                    l = LIST_1.sub(LIST_s, l)
                    l = LIST_2.sub(LIST_em, l)
                if '_' in l:
                    l = LIST_3.sub(LIST_s, l)
                    l = LIST_4.sub(LIST_em, l)

                if '[' in l:
                    if '!' in l:
                        _has_image = True
                        def IMG_REF_a(m):
                            _, v, id = m.groups()
                            id = ' '.join([s.strip() for s in (id or v).split('\n')])
                            if id not in self.markdown.urls:
                                return m.group(0)
                            url, title = self.markdown.urls[id]
                            return '<img src="{1}"{2} alt="{0}" \>'.format(v,
                            url, ' title="{0}"'.format(title) if title else '')
                    else:
                        _has_image = False


                    def URL_REF_a(m):
                        im, v, id = m.groups()
                        if im:
                            return IMG_REF_a(m)
                        id = ' '.join(
                            [s.strip() for s in (id or v).split('\n')])
                        _replaced = False
                        if '[' in v and ']' in v:
                            if _has_image:
                                v = IMG_REF.sub(IMG_REF_a, v)
                            v = URL_REF.sub(URL_REF_a, v)
                            _replaced = True
                        if id not in self.markdown.urls:
                            if _replaced:
                                return '['+v+']'
                            else:
                                return m.group(0)
                        url, title = self.markdown.urls[id]
                        return '<a href="{1}"{2}>{0}</a>'.format(v, url,
                            ' title="{0}"'.format(title) if title else '')

                    # The order of these subs is important.
                    l = URL.sub(URL_a, l)
                    l = URL_REF.sub(URL_REF_a, l)

                    if _has_image:
                        l = IMG.sub(IMG_img, l)
                        l = IMG_REF.sub(IMG_REF_a, l)

                if has_bs:
                    l = FIND_BS.sub('', l)
                strio.write(l)
            elif (i2 == -1 or i1 < i2) and i1 != -1 and l.count('`') > 1:
                # code span
                self._groupby(strio, '`', '`', l, CODE_SPAN,
                    lambda l:'<code>{0}</code>'.format(escape(
                            l[1:-1], quote=False)))
            else:
                # inlined html
                if HREF.search(l):
                    strio.write(HREF.sub(HREF_inline, l))
                else:
                    r = self._groupby(strio, '<', '>', l, INLINE_HTML)
                    if not r:
                        strio.write(l.replace('<', '&lt;'))
            
        if wrap:
            strio.write('</'+wrap+'>\n')
