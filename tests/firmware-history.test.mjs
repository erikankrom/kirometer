import assert from 'node:assert/strict';
import { updatesForDevice } from '../crew-app/ui/firmware-history.mjs';

const updates = [
  {id:'a', port:'/dev/cu.shared', device:{device_id:'a', usb_serial:'usb-a'}},
  {id:'b', port:'/dev/cu.shared', device:{device_id:'b', usb_serial:'usb-b'}},
  {id:'unknown', port:'/dev/cu.shared'},
];
assert.deepEqual(updatesForDevice(updates, {device_id:'a'}).map(j=>j.id), ['a']);
assert.deepEqual(updatesForDevice(updates, {device_id:'b'}).map(j=>j.id), ['b']);
assert.deepEqual(updatesForDevice(updates, {usb_serial:'usb-a'}).map(j=>j.id), ['a']);
assert.deepEqual(updatesForDevice(updates, {port:'/dev/cu.shared'}), []);
assert.deepEqual(updatesForDevice(updates, {}, 'unknown').map(j=>j.id), ['unknown']);
assert.deepEqual(updatesForDevice(updates, {device_id:'b', usb_serial:'usb-a'}).map(j=>j.id), ['b']);
assert.deepEqual(updatesForDevice(updates, {device_id:'b'}, 'a').map(j=>j.id), ['b']);
console.log('Device-scoped firmware history checks passed');
