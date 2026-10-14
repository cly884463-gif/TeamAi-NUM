"""Native input with verified embedded-page focus; no retries or content clearing."""
def prepare_active(timeout=12):
    def original(timeout):
        raise AssertionError('Build must inject the original navigation implementation')
    deadline=time.monotonic()+timeout
    target=original(timeout)
    _verify_target(target)
    page_target=next((t for t in _targets() if t.get('id')==target.page_id),None)
    if page_target is None:
        raise XiaodouyaError('抖音账号页已关闭，未上传。',code='invalid_page_identity')
    with _open(page_target) as page:
        while True:
            _verify_target(target)
            state=_state(page)
            try:
                _ensure_empty(state)
                return target
            except XiaodouyaError as e:
                if e.code!='page_loading' or time.monotonic()>=deadline:
                    raise
            time.sleep(.25)

def _ensure_empty(state):
    if state.get('pending'):
        raise XiaodouyaError('已进入抖音上传页，但抖音保留了上次未发布的视频。请在小豆芽页面选择“继续编辑”或确认“放弃”后再上传；本次未上传。',code='existing_content')
    if state.get('files') or state.get('videos') or state.get('text') or state.get('title'):
        raise XiaodouyaError('抖音当前页面已有视频或文案，本次未上传，未覆盖已有内容。',code='existing_content')
    if state.get('route')!=UPLOAD:
        raise XiaodouyaError('尚未进入抖音视频上传页，请重新检查所选账号与页面；本次未上传。',code='wrong_page')
    if state.get('inputs')!=1:
        raise XiaodouyaError('已进入抖音上传页，但上传控件尚未就绪或不唯一，请等待页面加载完成后重试；本次未上传。',code='page_loading')

def _focus_editor_end(page):
    if page._evaluate('document.hasFocus()') is not True:
        from xcl_publish.integrations.native_wechat import _targets, _open
        target = discover_active()
        _verify_target(target)
        if page._evaluate('performance.timeOrigin') != target.origin:
            raise XiaodouyaError('抖音页面已变化，停止填写。', code='description_mismatch')
        main = _open(next(t for t in _targets() if t.get('id') == target.main_id))
        try:
            focused = main._evaluate("""(() => {
              const views=Array.from(document.querySelectorAll('webview')).filter(v=>{
                const r=v.getBoundingClientRect();
                return r.width>0&&r.height>0&&getComputedStyle(v).visibility!=='hidden'&&
                  new URL(v.src).hostname==='creator.douyin.com';
              });
              if(views.length!==1)return false;
              views[0].focus();return document.activeElement===views[0];
            })()""")
            if focused is not True:
                raise XiaodouyaError('无法唯一确认抖音输入页面，停止填写。', code='description_mismatch')
        finally:
            main.close()
        _verify_target(target)
    moved = page._evaluate('''(() => {const editor=document.querySelector('''+json.dumps(EDITOR)+''');
      if(!editor||!document.hasFocus())return false;
      editor.focus();const selection=getSelection(),range=document.createRange();
      range.selectNodeContents(editor);range.collapse(false);selection.removeAllRanges();selection.addRange(range);
      return document.activeElement===editor&&document.hasFocus();})()''')
    if moved is not True:
        raise XiaodouyaError('抖音编辑焦点无法定位到文案末尾，停止填写。', code='description_mismatch')

def _insert(page, text):
    focused = page._evaluate('document.hasFocus()&&document.activeElement===document.querySelector('+json.dumps(EDITOR)+')')
    if focused is not True:
        raise XiaodouyaError('抖音编辑焦点已变化，停止填写。', code='description_mismatch')
    before = _state(page)['text']
    page._call('Input.insertText', {'text': text})
    after = _state(page)['text']
    if ' '.join(after.split()) != ' '.join((before+text).split()):
        raise XiaodouyaError('抖音文字未完整写入页面，停止填写，勿重复上传。', code='description_mismatch')

def fill_description(page, description, topics, verify_target):
    text=description.strip()
    verify_target()
    state=_state(page)
    if state['editors']!=1 or state['text'] or state['title']:
        raise XiaodouyaError('抖音描述框不唯一或已有文案，未覆盖。',code='existing_content')
    _focus_editor_end(page)
    _insert(page,text)
    selected=[]
    for topic in topics:
        verify_target()
        _focus_editor_end(page)
        _insert(page,' #'+topic)
        deadline=time.monotonic()+12
        while time.monotonic()<deadline:
            verify_target()
            if _topic_candidates(page,topic)==1:
                verify_target()
                if _topic_candidates(page,topic,click=True)!=1:
                    raise XiaodouyaError('抖音话题候选在选择前发生变化，请人工核对。',code='topic_not_confirmed')
                break
            time.sleep(.25)
        else:
            raise XiaodouyaError('未取得完全同名抖音话题，勿重复上传，请人工核对。',code='topic_not_confirmed')
        selected.append('#'+topic)
        expected=' '.join((text,*selected))
        # A visible #word is not proof that the asynchronous mention conversion completed.
        stable=0
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            verify_target()
            state=_state(page)
            matches=(_normalized_editor_text(state['text'])==_normalized_editor_text(expected)
                     and state['topics']==selected and not state['title'])
            stable=stable+1 if matches else 0
            if stable>=5:break
            time.sleep(.25)
        else:
            raise XiaodouyaError('抖音话题尚未稳定生效，停止后续输入；勿重复上传，请人工核对。',code='topic_not_confirmed')
    verify_target()
    page._evaluate('document.querySelector('+json.dumps(EDITOR)+').blur()')
    expected=' '.join((text,*selected))
    state=_wait_editor_stable(page,expected,verify_target)
    if state['topics']!=selected or state['title']:
        raise XiaodouyaError('抖音文案或话题读回不一致，请人工核对。',code='description_mismatch')
    return state
