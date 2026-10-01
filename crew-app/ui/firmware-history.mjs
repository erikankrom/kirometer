export function updatesForDevice(updates, device, currentJobId = null) {
  return updates.filter(job => {
    const recorded = job.device || {};
    if (device?.device_id) return recorded.device_id === device.device_id;
    if (device?.usb_serial) return recorded.usb_serial === device.usb_serial;
    return !!currentJobId && job.id === currentJobId;
  });
}
