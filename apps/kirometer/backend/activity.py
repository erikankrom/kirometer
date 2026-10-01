"""Read-only, version-bound Crew session activity; no conversation content."""
import time
import secrets

class ActivityTracker:
    def __init__(self):
        self.was_running=False
        self.completed_until=0
        self.monitor=None
        self.response_slots=None
        self.response_event=""

    def responses(self, slots):
        """One opaque event per newly waiting session; no IDs or content leave Crew.

        Initial discovery/recovery is silent. Repeated polls and other sessions'
        activity cannot replay a prompt. Approvals are intentionally not supported.
        """
        current=set(slots)
        if self.response_slots is not None and current-self.response_slots:
            self.response_event=secrets.token_hex(16)
        self.response_slots=current
        return {'needs_response':bool(current),'response_event':self.response_event}

    def classify(self, states, now=None, children=0):
        now=time.monotonic() if now is None else now
        if states is None:
            self.was_running=False;self.completed_until=0
            return 'unknown'
        active=bool(states) or children>0
        if any(s in ('waiting_permission','waiting_input') for s in states):value='attention'
        elif 'stalled' in states:value='error'
        elif active:value='working'
        else:
            if self.was_running:self.completed_until=now+8
            value='complete' if now<self.completed_until else 'idle'
        self.was_running=active
        if active:self.completed_until=0
        return value

    def read(self, state):
        try:
            if state is None or not isinstance(getattr(state,'_slots',None),dict):
                raise ValueError('No supported session state')
            from kiro_crew.dashboard.session_health import snapshot_state, SessionHealthMonitor
            if self.monitor is None:self.monitor=SessionHealthMonitor(include_log_scan=False)
            snap=snapshot_state(state)
            states=[];responses=[]
            for slot in snap.slots:
                health=self.monitor.classify_slot(slot,mono_now=snap.mono_now)
                if health is not None:
                    states.append(health.classification)
                    if health.classification=='waiting_input':responses.append(slot.key)
            value=self.classify(states,children=snap.subagents_running or 0)
            return {'activity':value,'activity_source':'kiro_crew_sessions','activity_scope':'crew','activity_available':True,**self.responses(responses)}
        except (ImportError,AttributeError,TypeError,ValueError):
            self.response_slots=None
            return {'needs_response':False,'response_event':self.response_event,'activity':self.classify(None),'activity_source':None,'activity_scope':'crew','activity_available':False}
