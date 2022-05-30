# MIT License
#
# Copyright (c) 2016 Alex Goodman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import difflib
import io
import sys

import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexer import RegexLexer
from pygments.lexers import guess_lexer_for_filename
from pygments.token import *

# Monokai is not quite right yet
PYGMENTS_STYLES = ["vs", "xcode"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html class="no-js">
    <head>
        <!-- 
          html_title:    browser tab title
          reset_css:     relative path to reset css file
          pygments_css:  relative path to pygments css file
          diff_css:      relative path to diff layout css file
          page_title:    title shown at the top of the page. This should be the filename of the files being diff'd
          original_code: full html contents of original file
          modified_code: full html contents of modified file
          jquery_js:     path to jquery.min.js
          diff_js:       path to diff.js
        -->
        <meta charset="utf-8">
        <title>
            %(html_title)s
        </title>
        <meta name="description" content="">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="mobile-web-app-capable" content="yes">
        <link rel="stylesheet" href="%(reset_css)s" type="text/css">
        <link rel="stylesheet" href="%(diff_css)s" type="text/css">
        <link class="syntaxdef" rel="stylesheet" href="%(pygments_css)s" type="text/css">
    </head>
    <body>
        <div class="" id="topbar">
          <input type="submit" value="Назад" onclick="window.location.href = '/solutions'">
          <div id="filetitle"> 
            %(page_title)s
          </div>
          <div class="switches">
            <div class="switch">
              <input id="highlight" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="highlight" data-on="&#10004; Highlight" data-off="Highlight"></label>
            </div>
            <div class="switch">
              <input id="codeprintmargin" class="toggle toggle-yes-no menuoption" type="checkbox" checked>
              <label for="codeprintmargin" data-on="&#10004; Margin" data-off="Margin"></label>
            </div>
          </div>
        </div>
        <div id="maincontainer" class="%(page_width)s">
            <div id="leftcode" class="left-inner-shadow codebox divider-outside-bottom">
                <div class="codefiletab">
                    &#10092; Original
                </div>
                <div class="printmargin">
                    01234567890123456789012345678901234567890123456789012345678901234567890123456789
                </div>
                %(original_code)s
            </div>
            <div id="rightcode" class="left-inner-shadow codebox divider-outside-bottom">
                <div class="codefiletab">
                    &#10093; Modified
                </div>
                <div class="printmargin">
                    01234567890123456789012345678901234567890123456789012345678901234567890123456789
                </div>
                %(modified_code)s
            </div>
        </div>
<script src="%(jquery_js)s" type="text/javascript"></script>
<script src="%(diff_js)s" type="text/javascript"></script>
    </body>
</html>
"""


class DefaultLexer(RegexLexer):
    """
    Simply lex each line as a token.
    """

    name = 'Default'
    aliases = ['default']
    filenames = ['*']

    tokens = {
        'root': [
            (r'.*\n', Text),
        ]
    }


class DiffHtmlFormatter(HtmlFormatter):
    """
    Formats a single source file with pygments and adds diff highlights based on the 
    diff details given.
    """
    isLeft = False
    diffs = None

    def __init__(self, isLeft, diffs, *args, **kwargs):
        self.isLeft = isLeft
        self.diffs = diffs
        super(DiffHtmlFormatter, self).__init__(*args, **kwargs)

    def wrap(self, source, outfile):
        return self._wrap_code(source)

    def getDiffLineNos(self):
        retlinenos = []
        for idx, ((left_no, left_line), (right_no, right_line), change) in enumerate(self.diffs):
            no = None
            if self.isLeft:
                if change:
                    if isinstance(left_no, int) and isinstance(right_no, int):
                        no = '<span class="lineno_q lineno_leftchange">' + str(left_no) + "</span>"
                    elif isinstance(left_no, int) and not isinstance(right_no, int):
                        no = '<span class="lineno_q lineno_leftdel">' + str(left_no) + "</span>"
                    elif not isinstance(left_no, int) and isinstance(right_no, int):
                        no = '<span class="lineno_q lineno_leftadd">  </span>'
                else:
                    no = '<span class="lineno_q">' + str(left_no) + "</span>"
            else:
                if change:
                    if isinstance(left_no, int) and isinstance(right_no, int):
                        no = '<span class="lineno_q lineno_rightchange">' + str(right_no) + "</span>"
                    elif isinstance(left_no, int) and not isinstance(right_no, int):
                        no = '<span class="lineno_q lineno_rightdel">  </span>'
                    elif not isinstance(left_no, int) and isinstance(right_no, int):
                        no = '<span class="lineno_q lineno_rightadd">' + str(right_no) + "</span>"
                else:
                    no = '<span class="lineno_q">' + str(right_no) + "</span>"

            retlinenos.append(no)

        return retlinenos

    def _wrap_code(self, source):
        source = list(source)
        yield 0, '<pre>'

        for idx, ((left_no, left_line), (right_no, right_line), change) in enumerate(self.diffs):
            # print idx, ((left_no, left_line),(right_no, right_line),change)
            try:
                if self.isLeft:
                    if change:
                        if isinstance(left_no, int) and isinstance(right_no, int) and left_no <= len(source):
                            i, t = source[left_no - 1]
                            t = '<span class="left_diff_change">' + t + "</span>"
                        elif isinstance(left_no, int) and not isinstance(right_no, int) and left_no <= len(source):
                            i, t = source[left_no - 1]
                            t = '<span class="left_diff_del">' + t + "</span>"
                        elif not isinstance(left_no, int) and isinstance(right_no, int):
                            i, t = 1, left_line
                            t = '<span class="left_diff_add">' + t + "</span>"
                        else:
                            raise
                    else:
                        if left_no <= len(source):
                            i, t = source[left_no - 1]
                        else:
                            i = 1
                            t = left_line
                else:
                    if change:
                        if isinstance(left_no, int) and isinstance(right_no, int) and right_no <= len(source):
                            i, t = source[right_no - 1]
                            t = '<span class="right_diff_change">' + t + "</span>"
                        elif isinstance(left_no, int) and not isinstance(right_no, int):
                            i, t = 1, right_line
                            t = '<span class="right_diff_del">' + t + "</span>"
                        elif not isinstance(left_no, int) and isinstance(right_no, int) and right_no <= len(source):
                            i, t = source[right_no - 1]
                            t = '<span class="right_diff_add">' + t + "</span>"
                        else:
                            raise
                    else:
                        if right_no <= len(source):
                            i, t = source[right_no - 1]
                        else:
                            i = 1
                            t = right_line
                yield i, t
            except:
                # print "WARNING! failed to enumerate diffs fully!"
                pass  # this is expected sometimes
        yield 0, '\n</pre>'

    def _wrap_tablelinenos(self, inner):
        dummyoutfile = io.StringIO()
        lncount = 0
        for t, line in inner:
            if t:
                lncount += 1

            # compatibility Python v2/v3
            if sys.version_info > (3, 0):
                dummyoutfile.write(line)
            else:
                print()
                dummyoutfile.write(str(line))

        fl = self.linenostart
        mw = len(str(lncount + fl - 1))
        sp = self.linenospecial
        st = self.linenostep
        la = self.lineanchors
        aln = self.anchorlinenos
        nocls = self.noclasses

        lines = []
        for i in self.getDiffLineNos():
            lines.append('%s' % (i,))

        ls = ''.join(lines)

        # in case you wonder about the seemingly redundant <div> here: since the
        # content in the other cell also is wrapped in a div, some browsers in
        # some configurations seem to mess up the formatting...
        if nocls:
            yield 0, ('<table class="%stable">' % self.cssclass +
                      '<tr><td><div class="linenodiv" '
                      'style="background-color: #f0f0f0; padding-right: 10px">'
                      '<pre style="line-height: 125%">' +
                      ls + '</pre></div></td><td class="code">')
        else:
            yield 0, ('<table class="%stable">' % self.cssclass +
                      '<tr><td class="linenos"><div class="linenodiv"><pre>' +
                      ls + '</pre></div></td><td class="code">')
        yield 0, dummyoutfile.getvalue()
        yield 0, '</td></tr></table>'


class Diff(object):
    """
    Manages a pair of source files and generates a single html diff page comparing
    the contents.
    """
    pygmentsCssFile = "web/resources/css/codeformats/%s.css"
    diffCssFile = "web/resources/css/diff.css"
    diffJsFile = "web/resources/js/diff.js"
    resetCssFile = "web/resources/css/reset.css"
    jqueryJsFile = "web/resources/js/jquery.min.js"

    def __init__(self, from_file: str, to_file: str, first_owner: str, second_owner: str):
        self.from_file = from_file
        self.to_file = to_file
        self.first_owner = first_owner
        self.second_owner = second_owner
        self.diffs = []
        self.html_contents = ""
        self.lexer = None

        def read_file(filename: str):
            try:
                with open(filename, encoding="utf-8") as file:
                    lines = file.readlines()
                    code = "".join(lines)
                    return lines, code
            except Exception as exception:
                print(f"Problem reading file {filename}")
                raise exception

        self.from_lines, self.left_code = read_file(self.from_file)
        self.to_lines, self.right_code = read_file(self.to_file)

    def format(self):
        def expand_tabs(line):
            line = line.replace(' ', '\0')
            line = line.expandtabs(8)
            line = line.replace(' ', '\t')
            return line.replace('\0', ' ').rstrip('\n')

        self.from_lines = [expand_tabs(line) for line in self.from_lines]
        self.to_lines = [expand_tabs(line) for line in self.to_lines]

        self.diffs = list(
            difflib._mdiff(self.from_lines, self.to_lines, linejunk=None, charjunk=difflib.IS_CHARACTER_JUNK)
        )

        fields = ((self.left_code, True, self.from_file),
                  (self.right_code, False, self.to_file))

        code_contents = []
        for (code, isLeft, filename) in fields:
            diff_html_formatter = DiffHtmlFormatter(isLeft, self.diffs, nobackground=False, linenos=True)

            try:
                self.lexer = guess_lexer_for_filename(self.to_file, code)
            except pygments.util.ClassNotFound:
                self.lexer = DefaultLexer()

            formatted = pygments.highlight(code, self.lexer, diff_html_formatter)
            code_contents.append(formatted)

        answers = {
            "html_title": "Сравнение",
            "reset_css": self.resetCssFile,
            "pygments_css": self.pygmentsCssFile % "vs",
            "diff_css": self.diffCssFile,
            "page_title": self.first_owner + " VS " + self.second_owner,
            "original_code": code_contents[0],
            "modified_code": code_contents[1],
            "jquery_js": self.jqueryJsFile,
            "diff_js": self.diffJsFile,
            "page_width": "page-full-width"
        }

        self.html_contents = HTML_TEMPLATE % answers


def compare(from_file, to_file, first_owner, second_owner):
    code_diff = Diff(from_file, to_file, first_owner, second_owner)
    code_diff.format()
    return code_diff.html_contents
