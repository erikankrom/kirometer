// Local-only test harness. All device operations below are simulated.
import * as React from "react";
import { createRoot } from "react-dom/client";
let scenario = "connected",
  sequence = 10;
const connected = () => ({
  connected: true,
  port: "test-bluetooth-device",
  transport: "bluetooth",
  message: "Usage delivered",
  status: {
    device_id: "test-device",
    touch_supported: true, touch_events: 12, swipe_events: 3, paired: true, uptime_seconds: 420, animation_interval_ms: 50,
    device_name: "Alex’s Kirometer",
    version: "0.9.0",
    controls_supported: true,
    screen_layouts_supported: true, screen_layouts_version: 2,
    screen_layout: "ghost", default_screen_layout: "ghost",
    bluetooth_supported: true,
    brightness: 180,
    sleep_mode: "auto",
    sleep_after: 120,
    battery_percent: 85,
    power_source: "usb",
    charging: false,
    sleeping: false,
    control_seq: sequence,
  },
});
let info = {
  supported: true,
  tools_ready: true,
  bluetooth_ready: true,
  default_name: "alex kirometer",
  ports: ["/dev/cu.test-device"],
  port_details: [{device:"/dev/cu.test-device",serial_number:"SAMPLE-USB-SERIAL",description:"USB JTAG/serial debug unit",vid:12346,pid:4097}],
  bundled_firmware: "/test/firmware.json",
  link: connected(),
  job: { id: "old-flash", kind: "flash", state: "complete", version: "0.9.0", device:{device_id:"test-device"} },
  firmware_updates: [{id:"mine",kind:"flash",state:"complete",version:"0.9.0",device:{device_id:"test-device",usb_serial:"SAMPLE-USB-SERIAL"},port:"/dev/cu.test-device",console:"Hash of data verified."},{id:"other",kind:"flash",state:"failed",version:"0.7.1",device:{device_id:"other-device"},port:"/dev/cu.test-device",console:"OTHER DEVICE LOG MUST NOT APPEAR"}],
};
const savedDevice = (id, name, online) => ({id, name, device_id:id, transport:"bluetooth", port:id, auto_connect:true,
  last_seen:Math.floor(Date.now()/1000)- (online ? 5 : 3600), last_status:{device_id:id,device_name:name,version:"0.9.0"},
  link:online ? {...connected(),status:{...connected().status,device_id:id,device_name:name}} : {connected:false,transport:"bluetooth",port:id,status:null,reconnecting:true,retry_in_seconds:160,message:"Unavailable"}});
info.devices = [savedDevice("home", "Home Kirometer", true), savedDevice("work", "Work Kirometer", false)];
const usage = {
  available: true,
  stale: false,
  age_seconds: 4,
  plan: "KIRO PRO",
  activity: "idle",
  activity_available: true,
  credits: [
    {
      used: 126,
      limit: 1000,
      used_percent: 12.6,
      remaining_plan_credits: 874,
      overage_used: 0,
      reset_at: "2026-11-01",
    },
  ],
};
let pollingSeconds = 300;
const api = {
  async get(path) {
    if (scenario === "error") throw Error("Offline");
    if (path.endsWith("/settings")) return {poll_seconds:pollingSeconds,activity_poll_ms:250};
    return structuredClone(path.endsWith("snapshot") ? usage : info);
  },
  async post(path, body) {
    const op = path.split("/").pop();
    if(op === "settings") {pollingSeconds=body.poll_seconds; return {poll_seconds:pollingSeconds};}
    if (op === "retry") {
      const device=info.devices.find(d=>d.id===body.configured_id);
      device.link={connected:false,connecting:true,status:null,transport:"bluetooth",port:device.id};
      setTimeout(()=>{Object.assign(device,savedDevice(device.id,device.name,true));},900);
      return {connecting:true,configured_id:device.id};
    }
    if (op === "controls") {
      const target=info.devices?.find(d=>d.id===body.configured_id);
      if(target) info.link=target.link;
      const seq = ++sequence;
      setTimeout(() => {
        Object.assign(info.link.status, body, { control_seq: seq });
        if (body.screen_layout) info.link.status.default_screen_layout=body.screen_layout;
        info.link.status.sleeping = body.sleep_mode === "sleep";
      }, 600);
      return { queued: true, control_seq: seq };
    }
    if (op === "disconnect") {
      const target=info.devices?.find(d=>d.id===body.configured_id);
      if(target) target.link={...target.link,connected:false,reconnecting:false,status:null,message:"Disconnected"};
      info.link = { connected: false, port: null, status: null };
      return info.link;
    }
    if (op === "bluetooth_scan")
      return {
        devices:
          scenario === "empty-scan"
            ? []
            : [{ name: "Alex’s Kirometer", address: "test-bluetooth-device" }],
      };
    if (op === "connect" || op === "bluetooth_connect") {
      info.link = connected();
      if (op === "connect") {
        info.link.transport = "usb";
        info.link.port = body.port;
      }
      return { connecting: true };
    }
    if (op === "bundle")
      return {
        version: "0.9.0",
        board: "waveshare-esp32-s3-touch-amoled-2.16",
        images: [{ offset: 0, size: 1024 }],
      };
    if (op === "setup" || op === "setup_bluetooth") {
      info.tools_ready = true;
      info.bluetooth_ready = true;
      return {};
    }
    if (op === "flash") {
      info.job = {
        id: "new-flash",
        kind: "flash",
        state: "running",
        message: "Installing…",
      };
      setTimeout(() => {
        info.job.state = "complete";
        info.job.version = "0.9.0";
      }, 600);
      return info.job;
    }
    return {};
  },
};
window.__kirocrew_modules = {
  react: React,
  "@kirocrew/app-sdk": { useAppApi: () => api },
};
const App = (await import("../../crew-app/ui/index.mjs")).default;
function Harness() {
  const [mode, setMode] = React.useState(new URLSearchParams(location.search).get("theme") || "light"),
    [revision, setRevision] = React.useState(0);
  return (
    <div data-theme={mode}>
      <nav className="test-tools" style={new URLSearchParams(location.search).has("screenshot") ? {display:"none"} : {}}>
        <strong>Simulated device · UI checks</strong>
        <button onClick={() => setMode(mode === "light" ? "dark" : "light")}>
          Switch to {mode === "light" ? "dark" : "light"}
        </button>
        <label>
          Scenario{" "}
          <select
            onChange={(e) => {
              scenario = e.target.value;
              info.devices=scenario === "multiple" ? [savedDevice("home","Home Kirometer",true),savedDevice("work","Work Kirometer",false)] : scenario === "empty" ? [] : [savedDevice("home","Home Kirometer",true)];
              info.link =
                scenario === "empty"
                  ? { connected: false, port: null, status: null }
                  : connected();
              setRevision((v) => v + 1);
            }}
          >
            <option value="multiple">Home and Work</option>
            <option value="connected">One device</option>
            <option value="empty">No device</option>
            <option value="error">API unavailable</option>
            <option value="empty-scan">No nearby devices</option>
          </select>
        </label>
      </nav>
      <App key={revision} />
    </div>
  );
}
createRoot(document.getElementById("root")).render(<Harness />);
