export function updatesForDevice(updates, device, currentJobId = null) {
  return updates.filter(job => {
    const recorded = job.device || {};
    if (device?.device_id) return recorded.device_id === device.device_id;
    if (device?.usb_serial) return recorded.usb_serial === device.usb_serial;
    return !!currentJobId && job.id === currentJobId;
  });
}

// Only advertise updates when both versions are known stable releases.
export function newerFirmware(installed, available) {
  const parse = value => typeof value === "string" && /^v?\d+\.\d+\.\d+(?:\+[\w.-]+)?$/.test(value)
    ? value.replace(/^v/, "").split("+")[0].split(".").map(Number) : null;
  const current = parse(installed), next = parse(available);
  if (!current || !next) return false;
  for (let i = 0; i < 3; i++) {
    if (next[i] !== current[i]) return next[i] > current[i];
  }
  return false;
}
