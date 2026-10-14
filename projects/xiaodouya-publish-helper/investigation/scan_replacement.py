def scan_opening_sentence(path, temporary_root, times=None, frame_reader=None,
                          text_reader=None, end_seconds=2.0, boundary_selector=None,
                          allow_extend=True, stop_at_punctuation=True, batch_text_reader=None):
    def original(path,temporary_root,times,frame_reader,text_reader,end_seconds,
                 boundary_selector,allow_extend,stop_at_punctuation,batch_text_reader):
        raise AssertionError('Build must inject recovered scanner')
    # The selected interval is authoritative; never silently add later narration.
    scan_times(end_seconds)  # Preserve original range validation.
    if times is None:
        limit=float(end_seconds)
        count=max(1,int(limit/.25))
        times=tuple(sorted(set([round(i*.25,3) for i in range(1,count+1) if i*.25<limit]
                              +[max(.01,round(limit-.01,3))])))
    result=original(path,temporary_root,times,frame_reader,text_reader,end_seconds,
                    None,False,stop_at_punctuation if boundary_selector is None else False,batch_text_reader)
    if boundary_selector is None:
        return result
    decision=boundary_selector(result)
    if decision.status=='complete':
        if not decision.text or not result.startswith(decision.text):
            raise ValueError('智能断句改写了原文，结果已拦截。')
        return decision.text
    if decision.status=='need_more' and not decision.text:
        # Successfully recognized text is still a candidate, not a verified sentence.
        # Draft.confirmed stays false; the operator can set a later explicit endpoint.
        return result
    raise ValueError('智能断句未能可靠判断文字，请定位句尾重新识别或人工核对。')
