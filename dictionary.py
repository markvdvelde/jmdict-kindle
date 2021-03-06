#
# Copyright 2014-2017 Jose Fonseca
# All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


import sys
import htmlmin

from collections import namedtuple
from html import escape

from kana import *
from cover import *

NAME_ENTRY, VOCAB_ENTRY = range(2)

Ortho = namedtuple('Ortho', ['value', 'rank', 'inflgrps'])


Sense = namedtuple('Sense', ['pos', 'dial', 'gloss'])

class Sentence:

    def __init__(self, english, japanese, good_sentence):
        self.english = english
        self.japanese =japanese
        self.good_sentence = good_sentence

class Entry:

    def __init__(self, label, senses, orthos, sentences=None, entry_type=VOCAB_ENTRY):
        self.label = label
        self.senses = senses
        self.orthos = orthos

        if(sentences == None):
            self.sentences = []
        else:
            self.sentences = sentences

        self.entry_type = entry_type

        self.headword = self._headword()
        self.section = self._section()

    def _headword(self):
        # Return the first hira/kata-kana word
        for ortho in self.orthos:
            reading = ortho.value
            if reading.startswith('っ'):
                reading = reading[1:]
            if is_kana(reading[:2]):
                return reading

        # Fallback to the first reading
        return self.orthos[0].value

    def _section(self):
        # Return the first syllable of the headword

        headword = self.headword

        initial = headword[0]
        if len(headword) > 1 and headword[1] in 'ゃャゅュょョァィゥェォ':
            initial += headword[1]

        return initial

    def remove(self, reading):
        assert isinstance(reading, str)
        for i in range(len(self.orthos)):
            ortho = self.orthos[i]
            if ortho.value == reading:
                self.orthos.pop(i)
                return
            else:
                for inflgrp_name, inflgrp_values in list(ortho.inflgrps.items()):
                    if reading in inflgrp_values:
                        inflgrp_values.discard(reading)
                        if not inflgrp:
                            del ortho.inflgrps[inflgrp_name]



def write_index_header(stream):
    stream.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    stream.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')
    stream.write('<html xmlns:mbp="https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf" xmlns:mmc="https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf" xmlns:idx="https://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf"\n')
    stream.write('<head>\n')
    stream.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n')
    stream.write('<link rel="stylesheet" type="text/css" href="style.css"/>\n')
    stream.write('</head>\n')
    stream.write('<body topmargin="0" bottommargin="0" leftmargin="0" rightmargin="0">\n')
    stream.write('<mbp:frameset>\n')


def write_index_footer(stream):
    stream.write('<mbp:pagebreak/>\n')
    stream.write('</mbp:frameset>\n')
    stream.write('</body>\n')
    stream.write('</html>\n')


def write_index(entries, dictionary_name, title, stream):
    # http://www.mobipocket.com/dev/article.asp?basefolder=prcgen&file=indexing.htm
    # http://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf
    # http://www.klokan.cz/projects/stardict-lingea/tab2opf.py

    # Sort entries alphabetically
    entries.sort(key=lambda x: x.headword)

    prev_section = None
    dictionary_file_name = dictionary_name.replace(' ', '_')

    stream = None

    sections = []
    section_streams = {}

    for entry in entries:
        section = entry.section

        if section != prev_section:
            try:
                stream = section_streams[section]
            except KeyError:
                sections.append(section)
                filename = 'entry-%s-%s.html'%(dictionary_file_name, section)
                stream = open(filename, 'wt', encoding='UTF-8')
                section_streams[section] = stream
                write_index_header(stream)

            prev_section = section

        #scriptable="yes" is needed, otherwise the results are cut off or results after the actual result are also dsiplayed
        stream.write('<idx:entry scriptable="yes">\n')#name attribute is omitted due to size constraints

        stream.write(' <p class=lab>' + escape(entry.label, quote=False) + '</p>\n')
        assert entry.senses
        
        if(len(entry.senses) > 0):
            stream.write(' <ul>\n')
            for sense in entry.senses:
                stream.write(' <li>')
                if sense.pos or sense.dial:
                    stream.write('<span class=pos>' + ','.join(sense.pos + sense.dial) + '</span> ')
                stream.write(escape('; '.join(sense.gloss), quote=False))
                stream.write('</li>\n')
            stream.write(' </ul>\n')

        if(entry.entry_type == VOCAB_ENTRY and len(entry.sentences) > 0):
            stream.write('<div class=ex>\n')
            stream.write(' <span class="exh">Examples:</span>\n')
            entry.sentences.sort(reverse=True, key = lambda sentence: sentence.good_sentence)
            for sentence in entry.sentences:
                stream.write(' <div class="sen">\n')
                stream.write('  <span>' + sentence.japanese + '</span>\n')
                stream.write('  <br>\n')
                stream.write('  <span>' + sentence.english + '</span>\n')
                stream.write(' </div>\n')
            stream.write('</div>\n')

        for ortho in entry.orthos:
            stream.write(' <idx:orth value="%s"' % escape(ortho.value, quote=True))
            if ortho.inflgrps:
                stream.write('>\n')
                for inflgrp in list(ortho.inflgrps.values()):
                    assert inflgrp
                    stream.write('  <idx:infl>\n')
                    iforms = list(inflgrp)
                    iforms.sort()
                    for iform in iforms:
                        stream.write('   <idx:iform value="%s"/>\n' % escape(iform, quote=True))
                    stream.write('  </idx:infl>\n')
                stream.write(' </idx:orth>\n')
            else:
                stream.write('/>\n')
        
        stream.write('</idx:entry>\n')
        
        stream.write('<hr/>\n')

    for stream in list(section_streams.values()):
        write_index_footer(stream)
        stream.close()

    #create cover
    createCover(dictionary_name, title, 768, 1024)

    # minify html
    minifier = htmlmin.Minifier(remove_empty_space=True)
    for i in range(len(sections)):
        section = sections[i]
        with open('entry-%s-%s.html' %(dictionary_file_name, section), 'r+', encoding='UTF-8') as f:
            content = f.read()
            content = minifier.minify(content)
            f.seek(0)
            f.write(content)
            f.truncate()


    # Write the OPF
    stream = open('%s.opf' %dictionary_file_name, 'wt', encoding='UTF-8')
    stream.write('<?xml version="1.0" encoding="utf-8"?>\n')
    stream.write('<package unique-identifier="uid">\n')
    stream.write('  <metadata>\n')
    stream.write('    <dc-metadata xmlns:dc="http://purl.org/metadata/dublin_core">\n')
    stream.write('      <dc:Identifier id="uid">%s</dc:Identifier>\n' %(hex(hash(title)).split('x')[1]))
    stream.write('      <dc:Title><h2>%s</h2></dc:Title>\n' %title)
    stream.write('      <dc:Language>ja</dc:Language>\n')
    stream.write('      <dc:Creator>Electronic Dictionary Research &amp; Development Group</dc:Creator>\n')
    stream.write('      <dc:Date>2019-05-08</dc:Date>\n')
    stream.write('      <dc:Copyrights>2013 Electronic Dictionary Research &amp; Development Group</dc:Copyrights>\n')
    stream.write('    </dc-metadata>\n')
    stream.write('    <x-metadata>\n')
    stream.write('      <output encoding="UTF-8" flatten-dynamic-dir="yes"/>\n')
    stream.write('      <DictionaryInLanguage>ja</DictionaryInLanguage>\n')
    stream.write('      <DictionaryOutLanguage>en</DictionaryOutLanguage>\n')
    #stream.write('      <DefaultLookupIndex>ja</DefaultLookupIndex>\n')  
    stream.write('    </x-metadata>\n')
    stream.write('  </metadata>\n')
    stream.write('  <manifest>\n')
    stream.write('    <item id="cover" href="%s-cover.jpg" media-type="image/jpeg" properties="cover-image"/>\n' %dictionary_file_name)
    stream.write('    <item id="css" href="style.css" media-type="text/css"/>\n')
    stream.write('    <item id="frontmatter" href="%s-frontmatter.html" media-type="text/x-oeb1-document"/>\n' %dictionary_file_name)
    for i in range(len(sections)):
        section = sections[i]
        stream.write('    <item id="entry-%u" href="entry-%s-%s.html" media-type="text/x-oeb1-document"/>\n' % (i, dictionary_file_name, escape(section, quote=True)))
    stream.write('  </manifest>\n')
    stream.write('\n')
    stream.write('  <spine>\n')
    stream.write('    <itemref idref="frontmatter"/>\n')
    for i in range(len(sections)):
        stream.write('    <itemref idref="entry-%u"/>\n' % i)
    stream.write('  </spine>\n')
    stream.write('  <tours/>\n')
    stream.write('  <guide/>\n')
    stream.write('</package>\n')
