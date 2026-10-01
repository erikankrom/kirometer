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
    device_name: "Alex’s Kirometer",
    version: "0.6.0",
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
  bundled_firmware: "/test/firmware.json",
  link: connected(),
  job: { id: "old-flash", kind: "flash", state: "complete", version: "0.6.0" },
};
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
const api = {
  async get(path) {
    if (scenario === "error") throw Error("Offline");
    return structuredClone(path.endsWith("snapshot") ? usage : info);
  },
  async post(path, body) {
    const op = path.split("/").pop();
    if (op === "controls") {
      const seq = ++sequence;
      setTimeout(() => {
        Object.assign(info.link.status, body, { control_seq: seq });
        if (body.screen_layout) info.link.status.default_screen_layout=body.screen_layout;
        info.link.status.sleeping = body.sleep_mode === "sleep";
      }, 600);
      return { queued: true, control_seq: seq };
    }
    if (op === "disconnect") {
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
        version: "0.6.0",
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
        info.job.version = "0.6.0";
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
              info.link =
                scenario === "empty"
                  ? { connected: false, port: null, status: null }
                  : connected();
              setRevision((v) => v + 1);
            }}
          >
            <option value="connected">Connected</option>
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
