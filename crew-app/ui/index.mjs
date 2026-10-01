import { icons, batteryIcon } from "./icons.mjs";
import { screenLayouts } from "./layouts.mjs";
const { react: React, "@kirocrew/app-sdk": sdk } = window.__kirocrew_modules;
const { createElement: h, useState, useEffect, useRef } = React;

// Inherit Crew's semantic palette so theme changes apply without a reload.
const styles = `
.km{--km-purple:#9147ff;--km-tint:color-mix(in srgb,var(--km-purple) 12%,var(--bg-elevated,#fff));color:var(--text,#211d26);font-family:inherit;max-width:1120px;margin:0 auto;padding:32px;line-height:1.5;font-variant-numeric:tabular-nums}
.km *{box-sizing:border-box}.km .km-icon{display:inline-flex;vertical-align:middle;flex-shrink:0;margin-right:7px}.km .km-icon svg{width:20px;height:20px}.km dd .km-icon{vertical-align:-4px}.km h1,.km h2,.km h3,.km p{margin:0}.km h1{font-size:32px;letter-spacing:-1px;font-weight:700}.km h2{font-size:23px;letter-spacing:-.5px}.km h3{font-size:17px}.km p{max-width:65ch}.km .muted{color:var(--muted-strong,var(--muted,#686170))}.km .small{font-size:13px}.km .eyebrow{font-size:12px;font-weight:650;letter-spacing:.07em;text-transform:uppercase;color:var(--muted,#686170)}
.km .row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.km .spread{justify-content:space-between}.km .stack{display:grid;gap:16px}.km .gap{margin-top:24px}.km .panel{background:var(--bg-elevated,#fff);border:1px solid var(--border,#ddd8e2);border-radius:16px;padding:24px}.km .subtle{background:var(--bg,#f5f3f8);border-radius:10px;padding:16px}.km .layout{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:24px;align-items:start}.km .device-head{display:flex;align-items:center;gap:16px}.km .device-title{overflow-wrap:anywhere}.km .device-icon{flex:0 0 64px;width:64px;height:64px;background:var(--km-tint);border-radius:18px;display:grid;place-items:center;color:var(--text,#211d26)}.km .device-icon svg{width:40px;height:40px}
.km button{appearance:none;font:inherit;font-size:14px;font-weight:600;cursor:pointer;border:1px solid var(--border-strong,var(--border,#d3cbdc));background:var(--bg-elevated,#fff);color:var(--text,#211d26);border-radius:9px;min-height:42px;padding:9px 15px;transition:background .15s,border-color .15s}.km button:hover:not(:disabled){background:var(--bg-hover,#eee8f5)}.km button:active:not(:disabled){transform:translateY(1px)}.km button.primary{background:var(--km-purple);border-color:var(--km-purple);color:white}.km button.primary:hover:not(:disabled){background:#7836dc}.km button.quiet{background:transparent;border-color:transparent}.km button:disabled{opacity:.46;cursor:not-allowed}.km :is(button,input,select,summary):focus-visible{outline:3px solid var(--km-purple);outline-offset:3px}.km button.danger{color:var(--danger,#b4233c)}
.km .badge{font-size:12px;font-weight:650;border-radius:6px;background:var(--km-tint);padding:4px 9px}.km .status{font-size:13px;display:inline-flex;align-items:center;gap:7px}.km .dot{width:7px;height:7px;border-radius:50%;background:var(--muted,#686170)}.km .online .dot{background:var(--ok,#218445)}.km .notice{padding:12px 15px;background:var(--bg,#f5f3f8);border-left:3px solid var(--km-purple);border-radius:5px;font-size:14px;overflow-wrap:anywhere}.km .notice.error{border-color:var(--danger,#b4233c);color:var(--danger,#b4233c)}.km .notice.success{border-color:var(--ok,#218445)}
.km .tabs{display:flex;gap:6px;border-bottom:1px solid var(--border,#ddd8e2);margin:24px -24px 20px;padding:0 24px;overflow:auto}.km .tabs button{border:0;border-radius:0;background:transparent;white-space:nowrap;padding:12px 8px;border-bottom:3px solid transparent;min-height:48px}.km .tabs button[aria-selected=true]{border-bottom-color:var(--km-purple);font-weight:750}.km .fields{display:grid;grid-template-columns:1fr 1fr;gap:20px}.km label.field{display:grid;gap:7px;font-size:14px;font-weight:600}.km label.field .hint{font-size:12px;font-weight:400;color:var(--muted-strong,var(--muted,#686170))}.km input:not([type=checkbox]):not([type=radio]):not([type=range]),.km select{font:inherit;font-size:15px;background:var(--bg,#f5f3f8);color:var(--text,#211d26);border:1px solid var(--border-strong,var(--border,#d3cbdc));border-radius:8px;padding:10px 12px;min-height:44px;width:100%}.km input[type=range]{width:100%;accent-color:var(--km-purple);min-height:32px}.km input[type=checkbox],.km input[type=radio]{accent-color:var(--km-purple);width:17px;height:17px;flex-shrink:0}.km fieldset{border:0;margin:0;padding:0;min-width:0}.km .save{border-top:1px solid var(--border,#ddd8e2);padding-top:18px;margin-top:20px}.km .numbers{font-size:32px;letter-spacing:-1px;font-weight:650;line-height:1.25}.km .meter{height:8px;border-radius:8px;background:var(--border,#ddd8e2);overflow:hidden;display:flex}.km .meter .used{background:var(--km-purple)}.km .meter .over{background:var(--danger,#b4233c)}.km dl{margin:0;display:grid;gap:12px}.km dl>div{display:flex;justify-content:space-between;gap:18px;font-size:13px}.km dt{color:var(--muted-strong,var(--muted,#686170))}.km dd{margin:0;text-align:right;overflow-wrap:anywhere}.km .divider{height:1px;background:var(--border,#ddd8e2)}.km .empty{display:grid;justify-items:start;gap:15px}.km .options{display:grid;grid-template-columns:1fr 1fr;gap:14px}.km .choice{text-align:left!important;padding:20px!important;display:grid;gap:6px}.km .choice span{font-weight:400;font-size:13px;color:var(--muted-strong,var(--muted,#686170))}.km .steps{list-style:none;padding:0;margin:20px 0;display:flex;gap:12px;font-size:13px}.km .steps li{flex:1;padding-top:9px;border-top:3px solid var(--border,#ddd8e2);color:var(--muted-strong,var(--muted,#686170))}.km .steps li.current{border-color:var(--km-purple);color:var(--text,#211d26);font-weight:650}.km .device-list{display:grid;gap:8px;padding:0;list-style:none;margin:0}.km .device-list li label{display:flex;gap:12px;align-items:center;padding:14px;border:1px solid var(--border,#ddd8e2);border-radius:9px;cursor:pointer}.km .device-list small{display:block;color:var(--muted-strong,var(--muted,#686170))}.km details summary{font-size:13px;cursor:pointer;color:var(--muted-strong,var(--muted,#686170));padding:8px 0}.km details>div{margin-top:10px}.km .confirm{display:flex;gap:10px;align-items:flex-start;font-size:13px}.km .footer{font-size:12px;color:var(--muted-strong,var(--muted,#686170));margin-top:20px}.km .loading{min-height:170px;display:grid;place-content:center;color:var(--muted,#686170)}
.km .layout-gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px;margin-top:12px}.km .screen-card{border:2px solid var(--border,#ddd8e2);border-radius:14px;padding:12px;display:grid;align-content:start;gap:12px;cursor:pointer;transition:border-color .15s,background .15s}.km .screen-card.selected{border-color:var(--km-purple);background:var(--km-tint)}.km .screen-card:has(input:focus-visible){outline:3px solid var(--km-purple);outline-offset:3px}.km .screen-card img{width:100%;height:auto;aspect-ratio:1;display:block;border-radius:9px;background:#000}.km .screen-card .card-title{display:flex;align-items:center;gap:8px;font-size:14px}.km .screen-card .card-title input{margin:0}.km .screen-card p{font-size:12px;color:var(--muted-strong,var(--muted,#686170));line-height:1.5}.km .screen-card .choice-state{font-size:11px;font-weight:600;color:var(--km-purple)}.km fieldset:disabled .screen-card{cursor:default}.km .firmware-console{background:#08080b;color:#e6e1ef;padding:16px;border-radius:10px;max-height:280px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.6 ui-monospace,monospace}.km summary{cursor:pointer}.km .gallery-legend{font-size:14px;font-weight:650}.km .gallery-note{margin-top:12px;font-size:12px;color:var(--muted-strong,var(--muted,#686170))}
@media(max-width:950px){.km .layout{grid-template-columns:1fr}.km aside{order:2}.km aside .stack{gap:12px}}@media(max-width:600px){.km{padding:18px}.km .panel{padding:18px}.km .fields,.km .options{grid-template-columns:1fr}.km .tabs{margin-left:-18px;margin-right:-18px;padding:0 18px}.km h1{font-size:28px}.km .device-icon{width:48px;height:48px;flex-basis:48px}.km .steps{gap:8px;font-size:12px}}
`;
const uiIcon = name => h("span", {className:"km-icon", "aria-hidden":true, dangerouslySetInnerHTML:{__html:icons[name] || ""}});
const num = (n) =>
  typeof n === "number"
    ? n.toLocaleString(undefined, { maximumFractionDigits: 2 })
    : "—";
const activityNames = {
  idle: "Ready",
  working: "Working",
  attention: "Needs attention",
  complete: "Complete",
  error: "Error",
  unknown: "Unknown",
};
const button = (text, onClick, disabled = false, kind = "") =>
  h("button", { type: "button", onClick, disabled, className: kind }, text);
const field = (text, control, hint) =>
  h(
    "label",
    { className: "field" },
    text,
    control,
    hint && h("span", { className: "hint" }, hint),
  );
// Same enclosure artwork as the Crew app listing; inherit the host palette.
const deviceIconSvg = "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 96 96\" fill=\"none\" role=\"img\" aria-label=\"Kirometer ghost enclosure\"><g transform=\"translate(52 46)\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M0,-39 C20,-39 29,-34 29,-24 C29,-8 29,12 25,28 C23,34 20,41 16,41 C14,41 12,41 10,41 C6,41 3,36 1,33 C-3,36 -6,41 -10,41 C-12,41 -14,41 -16,41 C-25,41 -26,31 -24,25 C-31,29 -37,26 -37,21 C-37,15 -30,10 -29,-1 C-29,-14 -30,-27 -22,-34 C-16,-38 -7,-39 0,-39 Z\" fill=\"currentColor\" fill-opacity=\".20\" stroke=\"currentColor\" stroke-width=\"6.8\" stroke-opacity=\".85\"/><rect x=\"-22.2\" y=\"-24.2\" width=\"44.4\" height=\"44.4\" rx=\"6.2\" fill=\"var(--km-purple)\" fill-opacity=\".12\" stroke=\"currentColor\" stroke-opacity=\".7\" stroke-width=\"4.8\"/><path d=\"M-14 11H14\" stroke=\"var(--km-purple)\" stroke-opacity=\".28\" stroke-width=\"4.8\"/><path d=\"M-14 11H3\" stroke=\"var(--km-purple)\" stroke-width=\"4.8\"/></g></svg>";
const deviceIcon = () => h("div", {className:"device-icon", "aria-hidden":true, dangerouslySetInnerHTML:{__html:deviceIconSvg}});
const statusPill = (online, text) =>
  h(
    "span",
    { className: "status" + (online ? " online" : "") },
    h("span", { className: "dot" }),
    text,
  );
function usePolling(api, path, ms) {
  const [state, setState] = useState({ data: null, error: false });
  useEffect(() => {
    let active = true,
      pending = false;
    const poll = async () => {
      if (pending) return;
      pending = true;
      try {
        const data = await api.get(path);
        if (active) setState({ data, error: false });
      } catch {
        if (active) setState((s) => ({ ...s, error: true }));
      } finally {
        pending = false;
      }
    };
    poll();
    const id = setInterval(poll, ms);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, [api, path, ms]);
  return state;
}
function UsageSummary({ data, error }) {
  const c = data?.credits?.[0],
    available = !error && data?.available,
    base = available ? Math.min(c?.used || 0, c?.limit || 0) : 0,
    over = available ? c?.overage_used || 0 : 0,
    total = Math.max(c?.limit || 0, base + over, 1);
  return h(
    "aside",
    { className: "panel stack", "aria-label": "Kiro usage" },
    h(
      "div",
      { className: "row spread" },
      h("h3", null, "Kiro usage"),
      h("span", { className: "badge" }, data?.plan || "Kiro"),
    ),
    h(
      "div",
      null,
      h("div", { className: "numbers" }, available ? num(c?.used) : "—"),
      h(
        "p",
        { className: "muted small" },
        available ? `of ${num(c?.limit)} monthly credits` : "Usage unavailable",
      ),
    ),
    h(
      "div",
      {
        className: "meter",
        role: "progressbar",
        "aria-label": "Plan usage",
        "aria-valuemin": 0,
        "aria-valuemax": 100,
        "aria-valuenow": available ? Math.min(c?.used_percent || 0, 100) : 0,
      },
      h("span", {
        className: "used",
        style: { width: (base / total) * 100 + "%" },
      }),
      h("span", {
        className: "over",
        style: { width: (over / total) * 100 + "%" },
      }),
    ),
    h(
      "dl",
      null,
      ...[
        ["Remaining", available ? num(c?.remaining_plan_credits) : "—"],
        ["Overage", available ? num(over) + " credits" : "—"],
        ["Activity", activityNames[data?.activity] || "Unknown"],
        ["Resets", c?.reset_at?.slice(0, 10) || "Unknown"],
      ].map(([k, v]) =>
        h("div", { key: k }, h("dt", null, k), h("dd", null, k === "Connection" && linked ? uiIcon(info?.link.transport === "bluetooth" ? "lucide-bluetooth" : "lucide-usb") : k === "Power" ? uiIcon(d?.battery_percent != null ? batteryIcon(d.battery_percent,d.charging) : d?.power_source === "usb" ? "lucide-plug" : "lucide-battery-warning") : null, v)),
      ),
    ),
    h("div", { className: "divider" }),
    h(
      "p",
      { className: "small muted" },
      error
        ? "Crew usage is temporarily unavailable."
        : !data?.available
          ? "Waiting for a usage reading."
          : `${data.stale ? "Cached usage · stale" : "Usage up to date"}${data.age_seconds != null ? " · " + num(data.age_seconds) + "s old" : ""}`,
    ),
  );
}
function AppSettings({api}) {
  const [saved, setSaved] = useState(null), [interval, setIntervalValue] = useState(300),
    [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  useEffect(()=>{
    let active=true;
    api.get("/api/apps/kirometer/settings").then(data=>{
      if(active){setSaved(data.poll_seconds);setIntervalValue(data.poll_seconds);}
    }).catch(()=>{if(active)setMessage("Could not load app settings. Reopen this page to retry.");});
    return ()=>{active=false;};
  },[api]);
  const saveSettings=async()=>{
    setBusy(true);setMessage("");
    try {
      const result=await api.post("/api/apps/kirometer/settings",{poll_seconds:interval});
      if(result.error)throw Error(result.error);
      setSaved(result.poll_seconds);setIntervalValue(result.poll_seconds);
      setMessage("Saved. Usage refresh timing updated; activity stays fast.");
    } catch(e){setMessage(e.message || "Settings could not be saved.");}
    finally{setBusy(false);}
  };
  return h("details",{className:"panel gap"},
    h("summary",null,"App settings"),
    h("div",{className:"stack"},
      field("Usage refresh interval (seconds)",h("input",{type:"number",min:5,max:3600,step:1,value:interval,disabled:saved===null || busy,onChange:e=>setIntervalValue(e.target.value===""?"":Number(e.target.value))}),"Default: 300 seconds (5 minutes). Applies to plan and overage credit reads. Range: 5–3,600 seconds."),
      h("p",{className:"small muted"},"Activity checks every 250 ms and sends changes immediately. A 5-second keepalive maintains the device connection. Usage refresh timing does not slow activity or device controls."),
      h("div",{className:"row"},button(busy?"Saving…":"Save app settings",saveSettings,busy || saved===null || saved===interval || !Number.isInteger(interval) || interval<5 || interval>3600,"primary")),
      message && h("p",{className:"small muted",role:"status"},message)));
}
export default function Kirometer() {
  const api = sdk.useAppApi(),
    usage = usePolling(api, "/api/apps/kirometer/snapshot", 1000);
  return h(
    "main",
    { className: "km" },
    h("style", null, styles),
    h(
      "header",
      { className: "row spread" },
      h(
        "div",
        null,
        h("h1", null, "Kirometer"),
        h("p", { className: "muted" }, "A little companion for your Kiro day."),
      ),
      statusPill(
        !usage.error && !!usage.data,
        usage.error
          ? "Crew unavailable"
          : usage.data
            ? "Connected to Crew"
            : "Connecting to Crew",
      ),
    ),
    h(DeviceManager, { api, usage }),
    h(AppSettings, { api }),
    h(
      "p",
      { className: "footer" },
      "Credits are cached separately from live activity. Usage comes from Crew’s billing cache, with the IDE cache as a fallback. Sync continues while this page is closed.",
    ),
  );
}
function DeviceManager({ api, usage }) {
  const polled = usePolling(api, "/api/apps/kirometer/devices", 2000);
  const [info, setInfo] = useState(null),
    [view, setView] = useState("manage"),
    [browseGallery, setBrowseGallery] = useState(false),
    [tab, setTab] = useState("screen"),
    [flow, setFlow] = useState(null),
    [step, setStep] = useState(1);
  const [port, setPort] = useState(""),
    [path, setPath] = useState(""),
    [bundle, setBundle] = useState(null),
    [confirmed, setConfirmed] = useState(false),
    [nearby, setNearby] = useState(null),
    [address, setAddress] = useState("");
  const [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [pending, setPending] = useState(null),
    [usbStatus, setUsbStatus] = useState(null),
    [flashId, setFlashId] = useState(null);
  const [draft, setDraft] = useState({
      device_name: "",
      brightness: 180,
      sound_enabled: false,
      sound_preset: "chime",
      sleep_mode: "auto",
      sleep_after: 120,
      screen_layout: "ghost",
    }),
    [dirty, setDirty] = useState(false);
  const deviceId = useRef(null);
  useEffect(() => {
    if (polled.data) setInfo(polled.data);
  }, [polled.data]);
  const d = info?.link?.status,
    linked = !!info?.link?.connected && !polled.error,
    running = !!busy || info?.job?.state === "running" || polled.error,
    controllable = linked && d?.controls_supported;
  useEffect(() => {
    if (!d) return;
    const changed = deviceId.current !== d.device_id;
    if (changed || !dirty) {
      setDraft({
        device_name: d.device_name || info.default_name || "",
        brightness: d.brightness ?? 180,
        sound_enabled: d.sound_enabled ?? false,
        sound_preset: d.sound_preset || "chime",
        sleep_mode: d.sleep_mode || "auto",
        sleep_after: d.sleep_after ?? 120,
        screen_layout: d.default_screen_layout || d.screen_layout || "ghost",
      });
      deviceId.current = d.device_id;
      if (changed) {
        setDirty(false);
        setPending(null);
      }
    }
  }, [
    d?.device_id,
    d?.device_name,
    d?.brightness,
    d?.sound_enabled,
    d?.sound_preset,
    d?.sleep_mode,
    d?.sleep_after,
    d?.screen_layout,
    d?.default_screen_layout,
    dirty,
    info?.default_name,
  ]);
  useEffect(() => {
    if (!pending) return;
    if (d?.control_seq === pending.seq) {
      if (pending.test) {
        setNotice(d.last_sound_test_seq === pending.seq ? "Kirometer accepted the test sound. Your saved settings are unchanged." : "The device could not play the test sound. Check its audio status.");
        setPending(null);
        return;
      }
      const matches = Object.entries(pending.values).every(
        ([k, v]) => (k === "screen_layout" ? d.default_screen_layout || d.screen_layout : d[k]) === v,
      );
      setNotice(
        matches
          ? "Saved on your Kirometer."
          : "The device responded with different settings. Review the confirmed values.",
      );
      setPending(null);
      if (matches) setDirty(false);
    }
  }, [d?.control_seq, pending]);
  useEffect(() => {
    if (!pending) return;
    const id = setTimeout(() => {
      setPending(null);
      setNotice(
        "Confirmation is taking longer than expected. Check the connection before saving again.",
      );
    }, 20000);
    return () => clearTimeout(id);
  }, [pending]);
  useEffect(() => {
    if (info?.ports?.length === 1 && !port) setPort(info.ports[0]);
    if (info?.bundled_firmware && !path) setPath(info.bundled_firmware);
  }, [info?.ports?.join("|"), info?.bundled_firmware, port, path]);
  const refresh = async () => {
    try {
      setInfo(await api.get("/api/apps/kirometer/devices"));
    } catch {
      setError("Cannot reach device manager. Try again.");
    }
  };
  const action = async (name, body = {}, done) => {
    setBusy(name);
    setError("");
    setNotice("");
    try {
      const result = await api.post(
        "/api/apps/kirometer/devices/" + name,
        body,
      );
      if (result.error) throw Error(result.error);
      done?.(result);
      await refresh();
      return result;
    } catch (e) {
      setError(e.message || "Device operation failed.");
      return null;
    } finally {
      setBusy("");
    }
  };
  const patch = (key, value) => {
    setDraft((v) => ({ ...v, [key]: value }));
    setDirty(true);
    setNotice("");
  };
  const nameBytes = new TextEncoder().encode(draft.device_name.trim()).length;
  const valid =
    nameBytes > 0 &&
    nameBytes <= 26 &&
    !/[\x00-\x1f\x7f]/.test(draft.device_name) &&
    Number.isInteger(draft.sleep_after) &&
    draft.sleep_after >= 30 &&
    draft.sleep_after <= 3600;
  const save = () => {
    const values = { ...draft, device_name: draft.device_name.trim() };
    if (!d?.screen_layouts_supported) delete values.screen_layout;
    if (!d?.sounds_supported) {delete values.sound_enabled; delete values.sound_preset;}
    action("controls", values, (r) => {
      setPending({ seq: r.control_seq, values });
      setNotice("Sent to device. Waiting for confirmation…");
    });
  };
  const testSound = () => {
    action("controls", {test_sound:draft.sound_preset}, (r) => {
      setPending({seq:r.control_seq,test:true});
      setNotice("Sending test sound to Kirometer…");
    });
  };
  const quickSleep = () => {
    const values = { sleep_mode: d?.sleeping ? "auto" : "sleep" };
    action("controls", values, (r) => {
      setPending({ seq: r.control_seq, values });
      setNotice("Waiting for the device…");
    });
  };
  const selectPort = (value) => {
    setPort(value);
    setUsbStatus(null);
    setConfirmed(false);
  };
  const portField = () =>
    field(
      "USB device",
      h(
        "select",
        {
          value: port,
          disabled: running,
          onChange: (e) => selectPort(e.target.value),
        },
        h(
          "option",
          { value: "" },
          info?.ports?.length ? "Choose a device" : "No USB device detected",
        ),
        ...(info?.ports || []).map((p) => h("option", { key: p, value: p }, p)),
      ),
    );
  const usbReady = info?.tools_ready && info?.ports?.includes(port);
  const connectUSB = () =>
    action("connect", { port }, () =>
      setNotice("Connecting over USB. This also prepares Bluetooth pairing."),
    );
  const connectBLE = () =>
    action("bluetooth_connect", { address }, () =>
      setNotice("Connecting over Bluetooth. Allow pairing if macOS prompts."),
    );
  const bluetooth = () =>
    h(
      "div",
      { className: "stack" },
      h(
        "div",
        null,
        h("h3", null, "Connect wirelessly"),
        h(
          "p",
          { className: "small muted" },
          "Find a Kirometer that has been set up on this Mac. A first-time device needs one USB connection to prepare Bluetooth.",
        ),
      ),
      !info.bluetooth_ready
        ? button(
            busy === "setup_bluetooth"
              ? "Installing…"
              : "Set up Bluetooth tools",
            () => action("setup_bluetooth"),
            running,
            "primary",
          )
        : h(
            React.Fragment,
            null,
            button(
              busy === "bluetooth_scan"
                ? "Searching…"
                : nearby
                  ? "Scan again"
                  : "Find nearby Kirometers",
              () =>
                action("bluetooth_scan", {}, (r) => {
                  setNearby(r.devices || []);
                  setAddress(
                    r.devices?.length === 1 ? r.devices[0].address : "",
                  );
                }),
              running,
            ),
            nearby &&
              nearby.length === 0 &&
              h(
                "p",
                { className: "notice" },
                "No Kirometers found. Check that the device is powered on and nearby, then scan again.",
              ),
            nearby?.length > 0 &&
              h(
                "ul",
                { className: "device-list" },
                ...nearby.map((n) =>
                  h(
                    "li",
                    { key: n.address },
                    h(
                      "label",
                      null,
                      h("input", {
                        type: "radio",
                        name: "nearby-device",
                        value: n.address,
                        checked: address === n.address,
                        onChange: () => setAddress(n.address),
                      }),
                      h(
                        "span",
                        null,
                        n.name || "Kirometer",
                        h(
                          "small",
                          null,
                          n.address === info?.link?.port
                            ? "Current device"
                            : "Available nearby",
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            nearby?.length > 0 &&
              button(
                "Connect selected device",
                connectBLE,
                running || !address,
                "primary",
              ),
          ),
      h(
        "p",
        { className: "small muted" },
        "One Kirometer can sync at a time. Connecting another device replaces the current connection.",
      ),
    );
  const firmware = () =>
    h(
      "div",
      { className: "stack" },
      h(
        "div",
        null,
        h(
          "h3",
          null,
          flow === "new" && view === "setup"
            ? "Install Kirometer firmware"
            : "Firmware",
        ),
        h(
          "p",
          { className: "small muted" },
          "Use a USB-C data cable for firmware updates. Bluetooth pairing and display settings are preserved.",
        ),
      ),
      !info.tools_ready &&
        button(
          "Install device tools",
          () => action("setup"),
          running,
          "primary",
        ),
      portField(),
      h(
        "div",
        { className: "row" },
        button("Refresh USB devices", refresh, running, "quiet"),
        button(
          busy === "bundle" ? "Checking…" : "Review bundled update",
          () => {
            setPath(info.bundled_firmware);
            action("bundle", { path: info.bundled_firmware }, (r) => {
              setBundle(r);
              setConfirmed(false);
            });
          },
          running,
          "primary",
        ),
      ),
      h(
        "details",
        null,
        h("summary", null, "Use a custom firmware bundle"),
        h(
          "div",
          { className: "stack" },
          field(
            "Bundle manifest path",
            h("input", {
              value: path,
              disabled: running,
              onChange: (e) => {
                setPath(e.target.value);
                setBundle(null);
                setConfirmed(false);
              },
              placeholder: "/path/to/firmware.json",
            }),
          ),
          button(
            "Review custom bundle",
            () =>
              action("bundle", { path }, (r) => {
                setBundle(r);
                setConfirmed(false);
              }),
            running || !path,
          ),
        ),
      ),
      bundle &&
        h(
          "div",
          { className: "subtle stack" },
          h(
            "div",
            { className: "row spread" },
            h("strong", null, "Kirometer " + bundle.version),
            h("span", { className: "badge" }, "Bundle verified"),
          ),
          h(
            "p",
            { className: "small muted" },
            "Waveshare ESP32-S3 Touch AMOLED 2.16 · " +
              bundle.images.length +
              " verified images",
          ),
          h(
            "label",
            { className: "confirm" },
            h("input", {
              type: "checkbox",
              checked: confirmed,
              disabled: running,
              onChange: (e) => setConfirmed(e.target.checked),
            }),
            h(
              "span",
              null,
              "Replace firmware on ",
              h("strong", null, port || "the selected device"),
              ". Keep the cable connected until the update finishes.",
            ),
          ),
          button(
            running ? "Please wait…" : "Install firmware",
            () =>
              action("flash", { path, port, confirm: true }, (r) => {
                setConfirmed(false);
                setFlashId(r.id);
              }),
            running || !confirmed || !usbReady,
            "primary",
          ),
        ),
      info.job?.kind === "flash" &&
        info.job.state === "complete" &&
        (view !== "setup" || info.job.id === flashId) &&
        h(
          "div",
          { className: "notice success" },
          linked && d?.version === info.job.version
            ? "Firmware " + d.version + " is running on your Kirometer."
            : "Firmware " +
                info.job.version +
                " was written and verified. Connect the device to confirm it has started.",
        ),
      info.job?.kind === "flash" &&
        info.job.state === "complete" &&
        !linked &&
        (view !== "setup" || info.job.id === flashId) &&
        button("Connect over USB", connectUSB, running || !usbReady),
    );
  const galleryBrowser = () => h("section", {className:"panel stack", "aria-label":"Screen gallery"},
    h("div", {className:"row spread"}, h("h2",null,"Screen gallery"), button("Close gallery",()=>setBrowseGallery(false))),
    h("p", {className:"small muted"},"Explore all six faces. Swipe left or right on your Kirometer to switch between them. Connect a device to choose its startup default."),
    h("div", {className:"layout-gallery"}, ...screenLayouts.map(layout => h("article",{key:layout.id,className:"screen-card"},
      h("img",{src:layout.preview,alt:layout.title+" screen preview",width:480,height:480}),
      h("h3",null,layout.title),h("p",null,layout.description),
      linked && h("span",{className:"choice-state"}, (d?.screen_layouts_version || 1) < (layout.capabilityVersion || 1) ? "Requires firmware "+layout.minimumFirmware : d?.screen_layout===layout.id ? "Current face" : "Available")))),
    linked && button("Customize default face",()=>{setBrowseGallery(false);setView("manage");setTab("screen");},running),
    h("p",{className:"gallery-note"},"Previews use sample data. All six faces are included in firmware 0.6.0. Extra-credit meters compare overage with the plan allowance."));
  const updateLog = () => {
    const updates = info?.firmware_updates?.length ? info.firmware_updates : info?.job?.kind === "flash" ? [info.job] : [];
    return h("section",{className:"panel stack","aria-label":"Firmware update history"},
      h("h3",null,"Firmware updates"),
      !updates.length ? h("p",{className:"small muted"},"Console output will appear here when you install firmware. The last eight updates are kept on this computer.") :
      updates.map((job,i)=>h("details",{key:job.id,open:i===0},
        h("summary",null,"Firmware "+(job.version || "update")+" · "+job.state+(job.started_at ? " · "+new Date(job.started_at*1000).toLocaleString():"")),
        h("p",{className:"small muted"},job.message),
        h("pre",{className:"firmware-console",tabIndex:0,"aria-label":"Firmware console output"},job.console || "No console output was recorded for this update."))));
  };
  const saveBar = () =>
      h(
        "div",
        { className: "row spread save" },
        h(
          "span",
          { className: "small muted" },
          pending
            ? "Waiting for device confirmation…"
            : dirty
              ? "Unsaved changes"
              : d?.brightness != null
                ? "Device settings are up to date."
                : "",
        ),
        h(
          "div",
          { className: "row" },
          dirty &&
            button(
              "Discard",
              () => {
                setDirty(false);
                setNotice("");
              },
              running || !!pending,
              "quiet",
            ),
          button(
            pending ? (pending.test ? "Testing…" : "Saving…") : "Save changes",
            save,
            running || !controllable || !dirty || !valid || !!pending,
            "primary",
          ),
        ),
      );
  const defaultScreen = () => h("div", {className:"stack"},
    h("fieldset", {disabled:running || !controllable || !!pending},
          h("fieldset", {disabled: !d?.screen_layouts_supported},
            h("legend", {className:"gallery-legend"}, "Screen gallery"),
            h("p", {className:"small muted"}, "Choose your default face. Save applies it now and at startup; swipe on the device to switch faces."),
            h("div", {className:"layout-gallery"}, ...screenLayouts.filter(layout => (d?.screen_layouts_version || 1)>= (layout.capabilityVersion || 1)).map(layout =>
              h("label", {key:layout.id,className:"screen-card"+(draft.screen_layout===layout.id?" selected":"")},
                h("img", {src:layout.preview,alt:layout.title+" screen preview",width:480,height:480}),
                h("div", {className:"card-title"},
                  h("input", {type:"radio",name:"kirometer-screen-layout","aria-label":layout.title,value:layout.id,checked:draft.screen_layout===layout.id,onChange:()=>patch("screen_layout",layout.id)}),
                  h("strong", null,layout.title)),
                h("p", null,layout.description),
                h("span", {className:"choice-state"}, draft.screen_layout===layout.id && draft.screen_layout!==(d?.default_screen_layout || d?.screen_layout)?"Selected default · save to apply":d?.screen_layout===layout.id?(d?.default_screen_layout || d?.screen_layout)===layout.id?"Current face · default":"Current face":(d?.default_screen_layout || d?.screen_layout)===layout.id?"Default at startup":"Available"),
              ))),
            h("p", {className:"gallery-note"}, !d?.screen_layouts_supported
              ? "Update to firmware 0.5.9 or later to choose a layout."
              : "Previews use sample data. Swipe left or right on any device screen to cycle all six faces. Swiping does not change your startup default. Overage meters compare extra credits with the plan allowance."),
          )),
    saveBar());
  const display = () =>
    h(
      "div",
      { className: "stack" },
      h(
        "div",
        null,
        h("h3", null, "Make it yours"),
        h(
          "p",
          { className: "small muted" },
          "Changes are saved on the device and confirmed here.",
        ),
      ),
      !d?.controls_supported &&
        h(
          "p",
          { className: "notice" },
          "Update the device firmware to enable customization.",
        ),
      h(
        "fieldset",
        { disabled: running || !controllable || !!pending },
        h(
          "div",
          { className: "stack" },
          field(
            "Device name",
            h("input", {
              value: draft.device_name,
              onChange: (e) => patch("device_name", e.target.value),
              "aria-invalid": nameBytes > 26 || !nameBytes,
            }),
            nameBytes > 26
              ? "Use no more than 26 UTF-8 bytes."
              : "Shown when you find your Kirometer over Bluetooth.",
          ),
          field(
            "Brightness · " + Math.round((draft.brightness / 255) * 100) + "%",
            h("input", {
              type: "range",
              min: 5,
              max: 255,
              value: draft.brightness,
              onChange: (e) => patch("brightness", Number(e.target.value)),
            }),
          ),
          h(
            "div",
            { className: "fields" },
            field(
              "Display sleep",
              h(
                "select",
                {
                  value: draft.sleep_mode,
                  onChange: (e) => patch("sleep_mode", e.target.value),
                },
                h("option", { value: "auto" }, "When Kiro is idle"),
                h("option", { value: "awake" }, "Keep screen awake"),
                h("option", { value: "sleep" }, "Start screensaver now"),
              ),
            ),
            field(
              "Idle timeout (seconds)",
              h("input", {
                type: "number",
                min: 30,
                max: 3600,
                value: draft.sleep_after,
                disabled: draft.sleep_mode !== "auto",
                onChange: (e) =>
                  patch(
                    "sleep_after",
                    e.target.value === "" ? "" : Number(e.target.value),
                  ),
              }),
              "30–3,600 seconds",
            ),
          ),
        ),
      ),
      h(
        "p",
        { className: "small muted" },
        "The black screensaver lets your ghost peek in occasionally. Touch the screen or press a top button to wake it.",
      ),
      h("fieldset",{disabled:running || !controllable || !!pending || !d?.sounds_supported || d?.audio_ready===false,className:"stack"},
        h("h3",null,"Notification sounds"),
        h("label",{className:"confirm"},h("input",{type:"checkbox",checked:draft.sound_enabled,onChange:e=>patch("sound_enabled",e.target.checked)}),"Enable sounds on Kirometer"),
        field("Needs Response sound",h("select",{value:draft.sound_preset,"aria-describedby":"km-sound-help",onChange:e=>patch("sound_preset",e.target.value)},
          ...["chime","ding","blip","pop","pulse"].map(t=>h("option",{key:t,value:t},t[0].toUpperCase()+t.slice(1))))),
        h("div",{className:"row"},button(pending?.test ? "Sending test…" : "Play test sound",testSound,!d?.test_sound_supported || !!pending || running)),
        h("p",{className:"small muted"},d?.test_sound_supported ? "Preview the selected sound on your device, even when alerts are off. Testing does not save changes." : "Update to firmware 0.7.1 or later to test sounds on the device."),
        h("p",{id:"km-sound-help",className:"small muted"},"Needs Response is the only supported alert so far. Your Kirometer plays the selected Kiro Crew sound once when a chat starts waiting for your reply. Repeated syncs and normal completion stay silent. Sounds are off by default; these settings do not change sounds on your computer."),
      ),
      !d?.sounds_supported && h("p",{className:"small muted"},"Update to firmware 0.7.0 or later to enable notification sounds."),
      d?.sounds_supported && d?.audio_ready===false && h("p",{className:"notice"},"Device audio could not initialize. Reconnect or restart your Kirometer before enabling sounds."),
      saveBar(),
    );
  const connection = () =>
    h(
      "div",
      { className: "stack" },
      h(
        "dl",
        null,
        ...[
          [
            "Connection",
            linked
              ? info?.link.transport === "bluetooth"
                ? "Bluetooth LE"
                : "USB"
              : "Disconnected",
          ],
          ["Device ID", d?.device_id || "—"],
          ["Firmware", d?.version || "—"],
          [
            "Power",
            d?.battery_percent != null
              ? `${d.battery_percent}% battery${d.charging ? " · charging" : d.power_source === "usb" ? " · plugged in" : ""}`
              : d?.power_source === "usb" ? "USB power · no battery" : "Power unknown",
          ],
        ].map(([k, v]) =>
          h("div", { key: k }, h("dt", null, k), h("dd", null, k === "Connection" && linked ? uiIcon(info?.link.transport === "bluetooth" ? "lucide-bluetooth" : "lucide-usb") : k === "Power" ? uiIcon(d?.battery_percent != null ? batteryIcon(d.battery_percent,d.charging) : d?.power_source === "usb" ? "lucide-plug" : "lucide-battery-warning") : null, v)),
        ),
      ),
      h(
        "div",
        { className: "row" },
        button("Refresh status", refresh, running),
        button(
          "Disconnect device",
          () => action("disconnect"),
          running || !info?.link?.port,
          "danger",
        ),
      ),
      h("div", { className: "divider" }),
      bluetooth(),
      h(
        "details",
        null,
        h("summary", null, "Connect using USB instead"),
        h(
          "div",
          { className: "stack" },
          portField(),
          button("Connect over USB", connectUSB, running || !usbReady),
          button(
            "Check USB firmware",
            () => action("status", { port }, setUsbStatus),
            running || !usbReady || !!info?.link?.port,
          ),
          usbStatus &&
            h(
              "p",
              { className: "notice" },
              usbStatus.firmware === "kirometer"
                ? "Kirometer firmware responding."
                : usbStatus.message || "Firmware could not be identified.",
            ),
        ),
      ),
    );
  const start = (type) => {
    setView("setup");
    setFlow(type);
    setStep(1);
    setFlashId(null);
    setError("");
    setNotice("");
  };
  const setup = () =>
    h(
      "section",
      { className: "panel stack" },
      h(
        "div",
        { className: "row spread" },
        h(
          "h2",
          null,
          flow === "new"
            ? "Set up a new Kirometer"
            : flow === "existing"
              ? "Connect your Kirometer"
              : "Add a device",
        ),
        button(
          "Back to devices",
          () => {
            setView("manage");
            setFlow(null);
            setNotice("");
          },
          running,
          "quiet",
        ),
      ),
      !flow
        ? h(
            "div",
            { className: "options" },
            button(
              h(
                React.Fragment,
                null,
                h("strong", null, "New device"),
                h(
                  "span",
                  null,
                  "Install firmware, then connect your Kirometer.",
                ),
              ),
              () => start("new"),
              running,
              "choice",
            ),
            button(
              h(
                React.Fragment,
                null,
                h("strong", null, "Already set up"),
                h(
                  "span",
                  null,
                  "Find and connect a device with Kirometer firmware.",
                ),
              ),
              () => start("existing"),
              running,
              "choice",
            ),
          )
        : flow === "existing"
          ? h(
              React.Fragment,
              null,
              bluetooth(),
              h(
                "details",
                null,
                h("summary", null, "First connection on this Mac? Use USB"),
                h(
                  "div",
                  { className: "stack" },
                  portField(),
                  !info.tools_ready &&
                    button(
                      "Install device tools",
                      () => action("setup"),
                      running,
                    ),
                  button(
                    "Connect and prepare Bluetooth",
                    connectUSB,
                    running || !usbReady,
                    "primary",
                  ),
                ),
              ),
            )
          : h(
              React.Fragment,
              null,
              h(
                "ol",
                { className: "steps" },
                ...["Prepare", "Install", "Connect"].map((s, i) =>
                  h(
                    "li",
                    {
                      key: s,
                      className: step === i + 1 ? "current" : "",
                      "aria-current": step === i + 1 ? "step" : undefined,
                    },
                    i + 1 + ". " + s,
                  ),
                ),
              ),
              step === 1
                ? h(
                    "div",
                    { className: "stack" },
                    h("h3", null, "Connect your device with USB"),
                    h(
                      "p",
                      { className: "muted" },
                      "Use a USB-C data cable with your Waveshare ESP32-S3 Touch AMOLED 2.16.",
                    ),
                    h(
                      "p",
                      { className: "small muted" },
                      info.tools_ready
                        ? "Device tools are ready."
                        : "Install the bundled tools once on this Mac. No separate terminal setup is needed.",
                    ),
                    !info.tools_ready &&
                      button(
                        "Install device tools",
                        () => action("setup"),
                        running,
                        "primary",
                      ),
                    portField(),
                    h(
                      "div",
                      { className: "row" },
                      button("Refresh devices", refresh, running),
                      button(
                        "Continue to firmware",
                        () => setStep(2),
                        running || !usbReady,
                        "primary",
                      ),
                    ),
                  )
                : step === 2
                  ? h(
                      React.Fragment,
                      null,
                      firmware(),
                      h(
                        "div",
                        { className: "row" },
                        button("Back", () => setStep(1), running, "quiet"),
                        button(
                          "Continue to connection",
                          () => setStep(3),
                          running ||
                            !(
                              info.job?.kind === "flash" &&
                              info.job?.state === "complete" &&
                              info.job?.id === flashId
                            ),
                          "primary",
                        ),
                      ),
                    )
                  : h(
                      "div",
                      { className: "stack" },
                      h("h3", null, "Bring your ghost online"),
                      h(
                        "p",
                        { className: "muted" },
                        "Connect over USB once to prepare pairing. Then switch to Bluetooth for wireless usage and controls.",
                      ),
                      button(
                        "Connect and prepare Bluetooth",
                        connectUSB,
                        running || !usbReady,
                        "primary",
                      ),
                      bluetooth(),
                    ),
            ),
      linked &&
        h(
          "div",
          { className: "subtle row spread" },
          h(
            "div",
            null,
            h("strong", null, d?.device_name || "Kirometer"),
            h(
              "p",
              { className: "small muted" },
              "Connected over " +
                (info?.link.transport === "bluetooth" ? "Bluetooth" : "USB"),
            ),
          ),
          button(
            "Customize device",
            () => {
              setView("manage");
              setTab("display");
              setFlow(null);
            },
            false,
            "primary",
          ),
        ),
    );
  return h(
    "div",
    { className: "gap stack" },
    h(
      "div",
      { className: "row spread" },
      h(
        "div",
        { className: "row" },
        h("h2", null, "Your devices"),
        h(
          "span",
          { className: "badge" },
          linked ? "1 connected" : "None connected",
        ),
      ),
      h("div",{className:"row"}, button("Browse screen gallery",()=>setBrowseGallery(v=>!v)), button(
        "Add a device",
        () => {
          setView("setup");
          setFlow(null);
          setError("");
          setNotice("");
        },
        running || view === "setup",
        "primary",
      )),
    ),
    browseGallery && galleryBrowser(),
    polled.error &&
      h(
        "p",
        { className: "notice error", role: "alert" },
        info
          ? "Device manager is unavailable. Showing the last known state; controls are paused."
          : "Device manager is unavailable. Retrying automatically…",
      ),
    error && h("p", { className: "notice error", role: "alert" }, error),
    notice && h("p", { className: "notice", role: "status" }, notice),
    info?.job?.state === "running" &&
      h(
        "p",
        { className: "notice", role: "status" },
        info.job.message || "Working…",
      ),
    info?.job &&
      ["failed", "interrupted"].includes(info.job.state) &&
      h(
        "p",
        { className: "notice error", role: "alert" },
        info.job.message || "The operation did not finish. Try again.",
      ),
    h(
      "div",
      { className: "layout" },
      !info
        ? h(
            "section",
            { className: "panel loading" },
            polled.error
              ? "Waiting for Crew to reconnect."
              : "Finding your devices…",
          )
        : !info.supported
          ? h(
              "section",
              { className: "panel" },
              "Device management currently supports macOS.",
            )
          : view === "setup"
            ? setup()
            : linked
              ? h(
                  "section",
                  { className: "panel" },
                  h(
                    "div",
                    { className: "row spread" },
                    h(
                      "div",
                      { className: "device-head" },
                      deviceIcon(),
                      h(
                        "div",
                        { className: "device-title" },
                        h("h2", null, d?.device_name || "Kirometer"),
                        h(
                          "p",
                          { className: "small muted" },
                          "Waveshare · 2.16″ AMOLED",
                        ),
                        statusPill(
                          true,
                          (info?.link.transport === "bluetooth"
                            ? "Bluetooth"
                            : "USB") + " connected",
                        ),
                      ),
                    ),
                    button(
                      d?.sleeping ? "Wake display" : "Preview screensaver",
                      quickSleep,
                      running || !controllable || dirty || !!pending,
                    ),
                  ),
                  h(
                    "nav",
                    {
                      className: "tabs",
                      role: "tablist",
                      "aria-label": "Device settings",
                    },
                    ...["screen", "display", "connection", "firmware"].map((t) =>
                      h(
                        "button",
                        {
                          key: t,
                          type: "button",
                          role: "tab",
                          tabIndex: tab === t ? 0 : -1,
                          onKeyDown: (event) => {
                            const tabs = ["screen", "display", "connection", "firmware"];
                            const delta =
                              event.key === "ArrowRight"
                                ? 1
                                : event.key === "ArrowLeft"
                                  ? -1
                                  : 0;
                            if (
                              delta ||
                              event.key === "Home" ||
                              event.key === "End"
                            ) {
                              event.preventDefault();
                              const next =
                                event.key === "Home"
                                  ? tabs[0]
                                  : event.key === "End"
                                    ? tabs[tabs.length - 1]
                                    : tabs[(tabs.indexOf(t) + delta + tabs.length) % tabs.length];
                              setTab(next);
                              document
                                .getElementById("km-tab-" + next)
                                ?.focus();
                            }
                          },
                          "aria-selected": tab === t,
                          "aria-controls": "km-panel-" + t,
                          id: "km-tab-" + t,
                          onClick: () => {
                            setTab(t);
                            setError("");
                            setNotice("");
                          },
                        },
                        t === "screen"
                          ? "Default screen"
                          : t === "display"
                          ? "Customize"
                          : t === "connection"
                            ? "Connection"
                            : "Firmware",
                      ),
                    ),
                  ),
                  h(
                    "div",
                    {
                      role: "tabpanel",
                      id: "km-panel-" + tab,
                      "aria-labelledby": "km-tab-" + tab,
                    },
                    tab === "screen"
                      ? defaultScreen()
                      : tab === "display"
                      ? display()
                      : tab === "connection"
                        ? connection()
                        : firmware(),
                  ),
                )
              : h(
                  "section",
                  { className: "panel empty" },
                  deviceIcon(),
                  h(
                    "h2",
                    null,
                    info?.link?.reconnecting
                      ? "Reconnecting to your Kirometer"
                      : info?.link?.port
                      ? info?.link?.message === "Connecting…"
                        ? "Connecting to your Kirometer"
                        : "Device needs attention"
                      : "Your ghost is waiting",
                  ),
                  h(
                    "p",
                    { className: "muted" },
                    info?.link?.port
                      ? info?.link.message
                      : "Set up a new device or reconnect one that already has Kirometer firmware.",
                  ),
                  h(
                    "div",
                    { className: "row" },
                    button(
                      "Connect existing device",
                      () => start("existing"),
                      running,
                      "primary",
                    ),
                    button("Set up a new device", () => start("new"), running),
                  ),
                  info?.link?.port &&
                    !linked &&
                    button(
                      "Cancel connection",
                      () => action("disconnect"),
                      running,
                      "quiet",
                    ),
                ),
      h(UsageSummary, usage),
    ),
    updateLog(),
  );
}
