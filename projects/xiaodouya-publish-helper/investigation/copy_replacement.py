"""Conservative local boundaries. Never shorten unknown text merely to fit a limit."""
def opening_prefix(sentence):
    import re
    text=sentence.strip()
    if not text:
        return ''
    # Audience callouts are complete opening utterances even when OCR drops punctuation.
    # Anchor at the start; do not match quoted/reported speech or questions such as
    # "朋友注意了哪些问题". No city or customer names participate in the rule.
    callout=re.match(
        r'^(?:在|家里|想要|准备|打算|需要|正在|有|各位|所有|厨房|卫生间)'
        r'[^。！？!?“”「」\n]{0,32}?(?:朋友们?|业主们?|老板们?)'
        r'[，,\s]*(?:注意了|注意啦|看过来|听好了)',text)
    if callout and not re.match(r'(?:哪些|什么|多少|没有|吗|呢|么)',text[callout.end():]):
        end=callout.end()
        if text[end:end+1] in ('。','！','!'):
            end+=1
        return text[:end]
    # Explicit punctuation is evidence of a boundary; do not slice a longer sentence.
    ending=re.search(r'[。！？!?]',text)
    if ending:
        return text[:ending.end()]
    # A repeated predicate begins another claim. Require the same complete predicate
    # and a nontrivial first complement; never deduplicate arbitrary repeated words.
    for match in re.finditer(r'(?:真正|确实)做到',text):
        lead=match.group()
        second=text.find(lead,match.end())
        if match.start()>=2 and second>=0:
            complement=text[match.end():second].strip(' ，,；;')
            prefix=text[:second].rstrip(' ，,；;')
            if len(complement)>=4 and not re.search(r'[？?]|不但|不仅|既要',prefix):
                # Only punctuation is added; all factual wording comes from the source.
                prefix=re.sub(r'^(在[^，。！？\s]{2,16})(我们)',r'\1，\2',prefix,count=1)
                return prefix+'。'
    return text

def publish_text_defaults(sentence):
    sentence=opening_prefix(sentence)
    return sentence, sentence if len(sentence)<=SHORT_TITLE_MAX_CHARS else ''
